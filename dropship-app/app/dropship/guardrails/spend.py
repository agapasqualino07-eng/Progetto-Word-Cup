"""Cap di spesa: per singola campagna e totale giornaliero."""

from decimal import Decimal

from dropship.guardrails.errors import SpendCapExceeded


class SpendGuard:
    def __init__(self, daily_cap, max_campaign_budget):
        self.daily_cap = Decimal(daily_cap)
        self.max_campaign_budget = Decimal(max_campaign_budget)

    def check(self, committed_today, requested):
        """``committed_today`` = budget giornalieri già impegnati (escluso quello in modifica)."""
        requested = Decimal(requested)
        if requested <= 0:
            raise SpendCapExceeded("budget richiesto deve essere > 0")
        if requested > self.max_campaign_budget:
            raise SpendCapExceeded(
                f"budget {requested} oltre il cap per campagna ({self.max_campaign_budget})"
            )
        total = Decimal(committed_today) + requested
        if total > self.daily_cap:
            raise SpendCapExceeded(
                f"spesa giornaliera totale {total} oltre il cap ({self.daily_cap})"
            )
