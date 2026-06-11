"""Test del backtester (meccanica ROI/CLV su dati di esempio)."""
import unittest

from src.backtest.backtester import Backtester
from src.backtest.sample_data import sample_history


class TestBacktester(unittest.TestCase):
    def test_runs_and_reports(self):
        res = Backtester().run()
        self.assertEqual(res.n_matches, len(sample_history()))
        self.assertGreaterEqual(res.n_bets, 0)
        self.assertLessEqual(res.n_bets, res.n_matches)

    def test_metrics_are_consistent(self):
        res = Backtester().run()
        if res.n_bets:
            # ROI coerente con profitto/puntato.
            self.assertAlmostEqual(res.roi, res.profit / res.total_staked, places=6)
            self.assertTrue(0.0 <= res.hit_rate <= 1.0)

    def test_summary_contains_verdict(self):
        text = Backtester().run().summary()
        self.assertTrue("PASS" in text or "FAIL" in text)

    def test_higher_min_edge_fewer_bets(self):
        few = Backtester(min_edge=0.20).run().n_bets
        many = Backtester(min_edge=0.01).run().n_bets
        self.assertLessEqual(few, many)


if __name__ == "__main__":
    unittest.main()
