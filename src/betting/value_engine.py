"""
Value engine — calcola il vantaggio (edge) e decide se una selezione ha valore.

Principio: si scommette solo quando la probabilità del modello supera quella
implicita nella quota di un margine sufficiente (>=5%). Sotto soglia → SKIP.
Questo è il principale antidoto al "bet su tutti i match" (errore KellyBench).
"""
from __future__ import annotations

from ..models.schemas import Selection

# Edge minimo per considerare una singola "di valore". Sotto → si salta.
MIN_EDGE_SINGLE = 0.05
# Edge minimo (combinato) per ammettere una gamba nelle combo.
MIN_EDGE_COMBO_LEG = 0.04


def implied_prob(odds: float) -> float:
    """Probabilità implicita grezza di una quota decimale."""
    return 1.0 / odds if odds > 0 else 0.0


def remove_margin(odds_1: float, odds_x: float, odds_2: float) -> dict[str, float]:
    """
    Rimuove il margine del bookmaker da un mercato 1X2 (metodo proporzionale).
    Restituisce le probabilità "fair" che sommano a 1. Utile per confronti
    onesti tra quote e modello.
    """
    raw = {
        "1": implied_prob(odds_1),
        "X": implied_prob(odds_x),
        "2": implied_prob(odds_2),
    }
    overround = sum(raw.values())
    if overround <= 0:
        return {k: 0.0 for k in raw}
    return {k: v / overround for k, v in raw.items()}


def bookmaker_margin(odds_1: float, odds_x: float, odds_2: float) -> float:
    """Margine (overround − 1) del book su un mercato 1X2. Es. 0.05 = 5%."""
    return implied_prob(odds_1) + implied_prob(odds_x) + implied_prob(odds_2) - 1.0


def has_value(selection: Selection, min_edge: float = MIN_EDGE_SINGLE) -> bool:
    """True se la selezione ha edge sufficiente per entrare nel piano."""
    return selection.edge >= min_edge


def expected_value(selection: Selection, stake: float) -> float:
    """
    EV monetario di una singola: prob_modello * profitto − prob_perdita * stake.
    Profitto netto su vincita = stake * (odds − 1).
    """
    p = selection.model_prob
    profit = stake * (selection.odds - 1.0)
    return round(p * profit - (1.0 - p) * stake, 2)


def filter_value_selections(
    selections: list[Selection], min_edge: float = MIN_EDGE_SINGLE
) -> list[Selection]:
    """Tiene solo le selezioni con edge sufficiente, ordinate per edge decrescente."""
    valued = [s for s in selections if has_value(s, min_edge)]
    return sorted(valued, key=lambda s: s.edge, reverse=True)
