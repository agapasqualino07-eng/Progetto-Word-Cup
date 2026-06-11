"""
Rating squadre REALI → forza attacco/difesa del modello Poisson.

Oggi il modello stima la forza con 4 "fasce" grossolane (constants.TEAM_TIERS).
Questo modulo permette di iniettare rating REALI e CONTINUI (es. ELO o punti
ranking FIFA) per partita: probabilità più realistiche → edge più affidabile.

Principio anti-allucinazione (CLAUDE.md):
  - Nessun rating viene inventato qui. Il file lo fornisci tu (o un fetch reale).
  - File assente → `None`: il modello ripiega sulle fasce (modalità base, dichiarata).
  - Riga malformata → errore esplicito, non un numero "indovinato".

Formato CSV (intestazione obbligatoria):
    team,rating
  - `team`   nome nazionale (come in constants.py, es. "Brasile")
  - `rating` numero di forza: qualunque scala monotona va bene (ELO, punti FIFA…).
             Conta la posizione RELATIVA fra le squadre, non il valore assoluto:
             i rating vengono normalizzati (z-score) e mappati su attacco/difesa.

File reale (non versionato): data/raw/team_ratings.csv
Template committato: data/team_ratings_template.csv
"""
from __future__ import annotations

import csv
import os
import statistics
from pathlib import Path

from .poisson_model import PoissonModel

DEFAULT_RATINGS_PATH = "data/raw/team_ratings.csv"
ENV_RATINGS_PATH = "WCE_RATINGS_CSV"

# Mappa z-score (deviazioni standard dalla media) → attacco/difesa, nella stessa
# scala "gol attesi" usata da constants. Trasparente e limitata; va affinata sul
# backtest. Convenzione difesa: più NEGATIVA = più forte (vedi poisson_model).
BASE_ATTACK = 1.35
ATTACK_PER_SD = 0.30
ATTACK_MIN, ATTACK_MAX = 0.70, 2.10
BASE_DEFENSE = -0.30
DEFENSE_PER_SD = 0.25
DEFENSE_MIN, DEFENSE_MAX = -0.78, 0.15


class RatingsLoadError(ValueError):
    """Errore di caricamento/validazione del file rating (messaggio esplicito)."""


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def parse_ratings_csv(text: str) -> dict[str, float]:
    """Valida e converte il CSV 'team,rating' in un dizionario {team: rating}."""
    rows = []
    for i, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        rows.append((i, raw))
    if not rows:
        raise RatingsLoadError("File rating vuoto: nessuna riga dati.")

    reader = csv.DictReader([content for _, content in rows])
    if reader.fieldnames is None:
        raise RatingsLoadError("Intestazione CSV mancante.")
    header = [h.strip() for h in reader.fieldnames]
    for col in ("team", "rating"):
        if col not in header:
            raise RatingsLoadError(
                f"Colonna '{col}' mancante. Intestazione attesa: team,rating."
            )

    ratings: dict[str, float] = {}
    for row, (src_line, _) in zip(reader, rows[1:]):
        team = (row.get("team") or "").strip()
        if not team:
            raise RatingsLoadError(f"Riga {src_line}: 'team' vuoto.")
        rating_raw = (row.get("rating") or "").strip()
        if not rating_raw:
            # Riga lasciata da compilare: la saltiamo (non inventiamo un valore).
            continue
        try:
            ratings[team] = float(rating_raw)
        except ValueError:
            raise RatingsLoadError(
                f"Riga {src_line}: rating non numerico per {team!r}: {rating_raw!r}"
            ) from None

    if len(ratings) < 2:
        raise RatingsLoadError(
            "Servono almeno 2 rating compilati per normalizzare (z-score)."
        )
    return ratings


def ratings_to_attack_defense(
    ratings: dict[str, float],
) -> tuple[dict[str, float], dict[str, float]]:
    """Trasforma i rating in dizionari attack/defense (z-score → scala gol)."""
    values = list(ratings.values())
    mean = statistics.mean(values)
    sd = statistics.pstdev(values)
    attack: dict[str, float] = {}
    defense: dict[str, float] = {}
    for team, r in ratings.items():
        z = (r - mean) / sd if sd > 0 else 0.0
        attack[team] = round(_clamp(BASE_ATTACK + z * ATTACK_PER_SD, ATTACK_MIN, ATTACK_MAX), 3)
        # Più forte (z alto) → difesa più negativa (concede meno).
        defense[team] = round(_clamp(BASE_DEFENSE - z * DEFENSE_PER_SD, DEFENSE_MIN, DEFENSE_MAX), 3)
    return attack, defense


def build_model_from_ratings(ratings: dict[str, float]) -> PoissonModel:
    """Costruisce un PoissonModel con i rating reali iniettati come prior."""
    attack, defense = ratings_to_attack_defense(ratings)
    return PoissonModel(attack=attack, defense=defense)


def load_ratings_model(path: str | os.PathLike | None = None) -> PoissonModel | None:
    """
    Carica i rating reali e restituisce un PoissonModel che li usa.
    Percorso: argomento > $WCE_RATINGS_CSV > default 'data/raw/team_ratings.csv'.
    File assente → None (il chiamante usa il modello base a fasce).
    File malformato → RatingsLoadError.
    """
    chosen = path or os.environ.get(ENV_RATINGS_PATH) or DEFAULT_RATINGS_PATH
    p = Path(chosen)
    if not p.exists():
        return None
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise RatingsLoadError(f"Impossibile leggere {p}: {exc}") from exc
    return build_model_from_ratings(parse_ratings_csv(text))
