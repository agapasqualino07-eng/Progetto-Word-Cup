import unittest
from decimal import Decimal

from dropship.catalog.pricing import (
    PricingError,
    charm_round_up,
    min_price,
    quote_at_price,
    suggest_price,
)
from dropship.config import PricingConfig

CFG = PricingConfig()


class TestPricing(unittest.TestCase):
    def test_vat_is_extracted_from_gross_price(self):
        q = quote_at_price(Decimal("10"), Decimal("2"), Decimal("122.00"), CFG)
        self.assertEqual(q.price_net, Decimal("100.00"))
        self.assertEqual(q.vat, Decimal("22.00"))

    def test_profit_accounts_for_cost_shipping_and_fees(self):
        q = quote_at_price(Decimal("10"), Decimal("2"), Decimal("122.00"), CFG)
        # fee = 122*0.029 + 0.30 = 3.838 -> 3.84
        self.assertEqual(q.payment_fees, Decimal("3.84"))
        self.assertEqual(q.landed_cost, Decimal("12.00"))
        self.assertEqual(q.profit, Decimal("84.16"))

    def test_min_price_hits_exact_min_margin(self):
        p = min_price(Decimal("10"), Decimal("3"), CFG)
        q = quote_at_price(Decimal("10"), Decimal("3"), p, CFG, rounding=False)
        self.assertAlmostEqual(float(q.margin), float(CFG.min_margin), places=6)

    def test_suggested_price_never_below_min_margin(self):
        for cost in ("1.50", "8", "23.70", "55"):
            q = suggest_price(Decimal(cost), Decimal("4.20"), CFG)
            self.assertGreaterEqual(q.margin, CFG.min_margin, cost)

    def test_market_price_used_when_above_minimum(self):
        q = suggest_price(Decimal("8"), Decimal("3"), CFG, market_price=Decimal("39.90"))
        self.assertEqual(q.price_gross, Decimal("39.90"))

    def test_market_price_below_minimum_is_ignored(self):
        q = suggest_price(Decimal("30"), Decimal("5"), CFG, market_price=Decimal("20"))
        self.assertGreater(q.price_gross, Decimal("20"))
        self.assertGreaterEqual(q.margin, CFG.min_margin)

    def test_charm_rounding(self):
        self.assertEqual(charm_round_up(Decimal("23.40")), Decimal("23.90"))
        self.assertEqual(charm_round_up(Decimal("23.95")), Decimal("24.90"))
        self.assertEqual(charm_round_up(Decimal("23.90")), Decimal("23.90"))

    def test_break_even_roas(self):
        q = quote_at_price(Decimal("10"), Decimal("2"), Decimal("122.00"), CFG)
        # 122 / 84.16 = 1.4496...
        self.assertEqual(q.break_even_roas, Decimal("1.45"))

    def test_non_positive_cost_rejected(self):
        with self.assertRaises(PricingError):
            suggest_price(Decimal("0"), Decimal("1"), CFG)

    def test_negative_shipping_rejected(self):
        with self.assertRaises(PricingError):
            suggest_price(Decimal("5"), Decimal("-1"), CFG)

    def test_impossible_margin_configuration_rejected(self):
        cfg = PricingConfig(min_margin=Decimal("0.99"), payment_fee_pct=Decimal("0.05"))
        with self.assertRaises(PricingError):
            min_price(Decimal("5"), Decimal("1"), cfg)

    def test_loss_making_price_has_no_break_even(self):
        q = quote_at_price(Decimal("50"), Decimal("5"), Decimal("20"), CFG)
        self.assertLess(q.profit, 0)
        self.assertIsNone(q.break_even_roas)


if __name__ == "__main__":
    unittest.main()
