"""
Backtest di ACCURATEZZA del modello su risultati REALI (niente quote).

Il backtest ROI/CLV (backtester.py) richiede le quote storiche, che non sempre
sono disponibili. Questo modulo valida invece il *cervello* del modello: quanto
le probabilità 1/X/2 stimate corrispondono agli esiti realmente accaduti.

Metriche (tutte: più basse = meglio, tranne hit-rate):
  - hit-rate : quante volte l'esito più probabile è quello uscito davvero.
  - Brier    : errore quadratico medio sulle 3 probabilità (0 = perfetto;
               0.667 = previsione uniforme 1/3-1/3-1/3).
  - log-loss : penalità logaritmica (0 = perfetto; 1.099 = uniforme).

Dati: risultati internazionali reali (data/intl_results_recent.csv), fonte
pubblica verificabile. Nessun dato inventato.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

from ..ml.poisson_model import PoissonModel

DEFAULT_RESULTS_PATH = "data/intl_results_recent.csv"


@dataclass
class RealMatch:
    date: str
    home: str
    away: str
    actual: str       # "1" | "X" | "2"
    neutral: bool


@dataclass
class AccuracyResult:
    n: int
    hit_rate: float
    brier: float
    log_loss: float

    def line(self, label: str) -> str:
        return (f"{label:22} n={self.n}  hit-rate={self.hit_rate:.1%}  "
                f"Brier={self.brier:.4f}  log-loss={self.log_loss:.4f}")


def load_results(path: str | Path = DEFAULT_RESULTS_PATH) -> list[RealMatch]:
    """Carica i risultati reali dal CSV (salta commenti e righe non valide)."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    data_lines = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    out: list[RealMatch] = []
    for row in csv.DictReader(data_lines):
        try:
            hs, as_ = int(row["home_score"]), int(row["away_score"])
        except (TypeError, ValueError, KeyError):
            continue
        actual = "1" if hs > as_ else ("X" if hs == as_ else "2")
        out.append(RealMatch(
            date=row.get("date", ""),
            home=row["home"].strip(),
            away=row["away"].strip(),
            actual=actual,
            neutral=(row.get("neutral", "").strip().lower() == "true"),
        ))
    return out


def evaluate_accuracy(model: PoissonModel, matches: list[RealMatch]) -> AccuracyResult:
    """Misura hit-rate, Brier e log-loss del modello sui risultati reali."""
    n = hit = 0
    brier = ll = 0.0
    for m in matches:
        venue = None if m.neutral else m.home
        p = model.predict_match(m.home, m.away, venue)
        probs = {"1": p.prob_1, "X": p.prob_x, "2": p.prob_2}
        if max(probs, key=probs.get) == m.actual:
            hit += 1
        for k in ("1", "X", "2"):
            y = 1.0 if k == m.actual else 0.0
            brier += (probs[k] - y) ** 2
        ll += -math.log(max(probs[m.actual], 1e-9))
        n += 1
    if n == 0:
        return AccuracyResult(0, 0.0, 0.0, 0.0)
    return AccuracyResult(n=n, hit_rate=hit / n, brier=brier / n, log_loss=ll / n)


if __name__ == "__main__":
    from ..ml.ratings_loader import load_ratings_model

    matches = load_results()
    print(f"Backtest di accuratezza su {len(matches)} partite reali "
          f"(fonte: martj42/international_results).\n")
    print(evaluate_accuracy(PoissonModel(), matches).line("Modello a FASCE"))
    ratings = load_ratings_model()
    if ratings is not None:
        print(evaluate_accuracy(ratings, matches).line("Rating FIFA reali"))
    print("\nNB: questo misura l'ACCURATEZZA delle probabilità, non il profitto.")
    print("    Il ROI/CLV richiede le quote storiche (vedi backtester.py).")
