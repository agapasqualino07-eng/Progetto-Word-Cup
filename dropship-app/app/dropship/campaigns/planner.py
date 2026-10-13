"""Regole di budget e stop-loss.

ROAS = ricavi lordi / spesa ads. Break-even ROAS = prezzo / profitto per unità:
sotto questa soglia ogni vendita da ads perde soldi -> STOP.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

CENT = Decimal("0.01")


@dataclass(frozen=True)
class StopLossDecision:
    action: str  # STOP | CONTINUE | DATI INSUFFICIENTI
    roas: Optional[Decimal]
    reason: str


def plan_budget(requested, cfg):
    requested = Decimal(requested)
    if requested <= 0:
        raise ValueError("il budget giornaliero deve essere > 0")
    return min(requested, cfg.max_campaign_budget).quantize(CENT, rounding=ROUND_HALF_UP)


def evaluate_stop_loss(spend, revenue, break_even_roas, min_spend):
    spend, revenue = Decimal(spend), Decimal(revenue)
    if spend < Decimal(min_spend):
        return StopLossDecision("DATI INSUFFICIENTI", None, f"spesa {spend} < {min_spend}: troppo presto per decidere")
    roas = (revenue / spend).quantize(CENT, rounding=ROUND_HALF_UP) if spend > 0 else Decimal("0")
    if break_even_roas is None:
        return StopLossDecision("STOP", roas, "prodotto senza profitto unitario: nessun ROAS è sostenibile")
    if roas < Decimal(break_even_roas):
        return StopLossDecision("STOP", roas, f"ROAS {roas} < break-even {break_even_roas}")
    return StopLossDecision("CONTINUE", roas, f"ROAS {roas} >= break-even {break_even_roas}")
