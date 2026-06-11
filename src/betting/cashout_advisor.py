"""
Cashout advisor — consiglio live sulle bet in corso.

Valuta l'EV residuo dalla probabilità live e applica trigger rigidi
(gol contro tardivo, espulsione nostra → CASHOUT; gol nostro tardivo → MANTIENI).
Nessuna quota/probabilità inventata: la prob live va passata dall'esterno
(modello live o feed). Se manca → INSUFFICIENTE.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CashoutDecision(str, Enum):
    CASHOUT = "CASHOUT ORA"
    HOLD = "HOLD"
    MANTIENI = "MANTIENI"
    INSUFFICIENTE = "INSUFFICIENTE"


@dataclass
class MatchState:
    minute: int
    live_prob: float | None = None      # prob. che la nostra bet vinca, ora
    red_card_our_team: bool = False
    goal_against_after_60: bool = False
    goal_for_after_75: bool = False


# Ogni quanto ricontrollare (secondi) per fascia di minuti — usato dallo scheduler.
CHECK_INTERVALS = {"0-15": 300, "15-60": 180, "60-75": 120, "75-90": 60}


def evaluate(potential_payout: float, stake: float, state: MatchState) -> CashoutDecision:
    """Decisione di cashout. EV residuo = p·payout − (1−p)·stake."""
    # Trigger rigidi (non dipendono dalla prob live).
    if state.red_card_our_team:
        return CashoutDecision.CASHOUT
    if state.goal_against_after_60:
        return CashoutDecision.CASHOUT
    if state.goal_for_after_75 and (state.live_prob or 0) > 0.75:
        return CashoutDecision.MANTIENI

    if state.live_prob is None:
        return CashoutDecision.INSUFFICIENTE  # niente dati → nessun consiglio

    p = state.live_prob
    ev_residuo = p * potential_payout - (1.0 - p) * stake
    if ev_residuo < -0.05 * stake:
        return CashoutDecision.CASHOUT
    if p > 0.80 and state.minute > 75:
        return CashoutDecision.MANTIENI
    return CashoutDecision.HOLD
