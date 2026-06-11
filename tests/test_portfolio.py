"""Test del portafoglio persistente (SQLite in memoria)."""
import unittest
from datetime import date

from src.data.odds_api import mock_matchday
from src.portfolio.tracker import PortfolioTracker
from src.services.pipeline import generate_plan


class TestPortfolio(unittest.TestCase):
    def setUp(self):
        self.t = PortfolioTracker(db_path=":memory:", initial_bankroll=100.0)

    def tearDown(self):
        self.t.close()

    def test_initial_bankroll(self):
        self.assertEqual(self.t.bankroll, 100.0)

    def test_confirm_and_settle_win(self):
        plan = generate_plan(mock_matchday(), 100.0, date(2026, 6, 16))
        ids = self.t.confirm_plan(plan)
        self.assertEqual(len(ids), len(plan.all_bets))
        if ids:
            profit = self.t.settle(ids[0], won=True)
            self.assertGreater(profit, 0)
            self.assertGreater(self.t.bankroll, 100.0)

    def test_settle_loss_reduces_bankroll(self):
        plan = generate_plan(mock_matchday(), 100.0, date(2026, 6, 16))
        ids = self.t.confirm_plan(plan)
        if ids:
            self.t.settle(ids[0], won=False)
            self.assertLess(self.t.bankroll, 100.0)

    def test_double_settle_raises(self):
        plan = generate_plan(mock_matchday(), 100.0, date(2026, 6, 16))
        ids = self.t.confirm_plan(plan)
        if ids:
            self.t.settle(ids[0], won=True)
            with self.assertRaises(ValueError):
                self.t.settle(ids[0], won=True)

    def test_summary_roi_consistent(self):
        plan = generate_plan(mock_matchday(), 100.0, date(2026, 6, 16))
        ids = self.t.confirm_plan(plan)
        for i, bid in enumerate(ids):
            self.t.settle(bid, won=(i % 2 == 0))
        s = self.t.summary()
        self.assertEqual(s.n_settled, len(ids))
        self.assertEqual(s.n_bets, len(ids))


if __name__ == "__main__":
    unittest.main()
