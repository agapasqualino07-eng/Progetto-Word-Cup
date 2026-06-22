"""Test dello scoreboard prestazioni su partite reali."""
import unittest

from src.backtest.sample_data import HistoricalMatch
from src.services.performance import (
    MIN_MEANINGFUL,
    Performance,
    StrategyResult,
    evaluate_performance,
    format_performance_report,
)


def _hm(home, away, actual, o1, ox, o2):
    # apertura = chiusura per semplicità nei test
    return HistoricalMatch(home, away, actual, o1, ox, o2, o1, ox, o2)


class TestStrategyResult(unittest.TestCase):
    def test_roi_computation(self):
        s = StrategyResult("x", n_bets=10, n_wins=4, profit=20.0)
        self.assertAlmostEqual(s.roi, 20.0 / 100.0)

    def test_roi_zero_bets(self):
        self.assertEqual(StrategyResult("x", 0, 0, 0.0).roi, 0.0)


class TestEvaluate(unittest.TestCase):
    def test_hit_rate_and_flat_profit(self):
        # Favorita nettissima che vince: il pronostico la prende, flat in profitto
        # solo se la quota copre... a 1.10 (vinta) profitto +1.0; impostiamo 2 match.
        history = [
            _hm("Brasile", "Haiti", "1", 1.10, 9.0, 20.0),     # prevista 1, esce 1
            _hm("Spagna", "Capo Verde", "1", 1.20, 7.0, 15.0),  # prevista 1, esce 1
        ]
        perf = evaluate_performance(history)
        self.assertEqual(perf.n_matches, 2)
        self.assertEqual(perf.pronostici_correct, 2)
        self.assertGreater(perf.flat_open.profit, 0)   # due favorite vinte

    def test_report_flags_small_sample(self):
        history = [_hm("Brasile", "Haiti", "1", 1.10, 9.0, 20.0)]
        perf = evaluate_performance(history)
        self.assertFalse(perf.meaningful)
        text = format_performance_report(perf)
        self.assertIn("campione PICCOLO", text)
        self.assertIn("Pronostici azzeccati", text)

    def test_meaningful_threshold(self):
        history = [_hm("Brasile", "Haiti", "1", 1.5, 4.0, 7.0)] * MIN_MEANINGFUL
        perf = evaluate_performance(history)
        self.assertTrue(perf.meaningful)
        self.assertNotIn("campione PICCOLO", format_performance_report(perf))


if __name__ == "__main__":
    unittest.main()
