"""
Taratura del modello su risultati REALI — con validazione train/test onesta.

Cerca i parametri (rho Dixon-Coles, vantaggio campo, scala dei rating) che
minimizzano il log-loss sulle partite di TRAIN (2024-25) e li giudica sulle
partite di TEST (2026), MAI viste durante la ricerca. Solo se migliorano sul
test vengono adottati come default.

Tutto standard library. Eseguibile:  python -m src.ml.tuning
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import product

from ..backtest.accuracy import RealMatch, evaluate_accuracy, load_results
from .poisson_model import PoissonModel
from .ratings_loader import (
    DEFAULT_RATINGS_PATHS,
    parse_ratings_csv,
)
from pathlib import Path

TRAIN_BEFORE = "2026-01-01"   # train: 2024-25 · test: 2026


@dataclass(frozen=True)
class TunedParams:
    rho: float
    home_adv: float
    attack_per_sd: float
    defense_per_sd: float


def _load_ratings() -> dict[str, float]:
    for p in DEFAULT_RATINGS_PATHS:
        if Path(p).exists():
            return parse_ratings_csv(Path(p).read_text(encoding="utf-8"))
    raise FileNotFoundError("file rating non trovato (data/team_ratings.csv)")


def model_with(params: TunedParams, ratings: dict[str, float]) -> PoissonModel:
    """Costruisce il modello dai rating con la scala/parametri indicati."""
    import statistics

    values = list(ratings.values())
    mean, sd = statistics.mean(values), statistics.pstdev(values)
    attack, defense = {}, {}
    for team, r in ratings.items():
        z = (r - mean) / sd if sd > 0 else 0.0
        attack[team] = max(0.70, min(2.10, 1.35 + z * params.attack_per_sd))
        defense[team] = max(-0.78, min(0.15, -0.30 - z * params.defense_per_sd))
    return PoissonModel(attack=attack, defense=defense,
                        rho=params.rho, home_adv=params.home_adv)


def split_matches() -> tuple[list[RealMatch], list[RealMatch]]:
    matches = load_results()
    train = [m for m in matches if m.date < TRAIN_BEFORE]
    test = [m for m in matches if m.date >= TRAIN_BEFORE]
    return train, test


def grid_search(train: list[RealMatch], ratings: dict[str, float]) -> TunedParams:
    """Minimizza il log-loss sul train. Griglia volutamente grossolana
    (4 parametri, pochi valori) per limitare l'overfitting su ~245 partite."""
    grid = {
        "rho": [0.0, -0.05, -0.10, -0.15],
        "home_adv": [0.0, 0.10, 0.20, 0.30],
        "attack_per_sd": [0.20, 0.30, 0.40],
        "defense_per_sd": [0.15, 0.25, 0.35],
    }
    best, best_ll = None, math.inf
    for rho, ha, aps, dps in product(*grid.values()):
        params = TunedParams(rho, ha, aps, dps)
        res = evaluate_accuracy(model_with(params, ratings), train)
        if res.log_loss < best_ll:
            best, best_ll = params, res.log_loss
    return best


def main() -> None:
    train, test = split_matches()
    ratings = _load_ratings()
    print(f"Train: {len(train)} partite (2024-25) · Test: {len(test)} partite (2026)\n")

    baseline = TunedParams(rho=0.0, home_adv=0.0, attack_per_sd=0.30, defense_per_sd=0.25)
    base_train = evaluate_accuracy(model_with(baseline, ratings), train)
    base_test = evaluate_accuracy(model_with(baseline, ratings), test)
    print(base_train.line("BASE   (train)"))
    print(base_test.line("BASE   (test) "))

    tuned = grid_search(train, ratings)
    t_train = evaluate_accuracy(model_with(tuned, ratings), train)
    t_test = evaluate_accuracy(model_with(tuned, ratings), test)
    print(f"\nParametri tarati: rho={tuned.rho} home_adv={tuned.home_adv} "
          f"attack/sd={tuned.attack_per_sd} defense/sd={tuned.defense_per_sd}")
    print(t_train.line("TARATO (train)"))
    print(t_test.line("TARATO (test) "))

    verdict = ("✅ MIGLIORA anche sul test mai visto → adottabile."
               if t_test.log_loss < base_test.log_loss else
               "❌ NON migliora sul test → NON adottare (overfitting).")
    print(f"\n{verdict}")


if __name__ == "__main__":
    main()
