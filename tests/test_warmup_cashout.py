"""Test del warm-up manager e del cashout advisor."""
import unittest
from datetime import date

from src.betting.cashout_advisor import CashoutDecision, MatchState, evaluate
from src.betting.warmup import phase_for, warmup_stake


class TestWarmup(unittest.TestCase):
    def test_phases_by_date(self):
        self.assertEqual(phase_for(date(2026, 6, 13)).nome, "osservazione")
        self.assertEqual(phase_for(date(2026, 6, 20)).nome, "cautela")
        self.assertEqual(phase_for(date(2026, 6, 26)).nome, "normale")
        self.assertEqual(phase_for(date(2026, 7, 5)).nome, "knockout")

    def test_warmup_reduces_early_stake(self):
        self.assertEqual(warmup_stake(10.0, date(2026, 6, 13)), 5.0)   # ×0.5
        self.assertEqual(warmup_stake(10.0, date(2026, 6, 26)), 10.0)  # ×1.0


class TestCashout(unittest.TestCase):
    def test_red_card_triggers_cashout(self):
        st = MatchState(minute=50, live_prob=0.6, red_card_our_team=True)
        self.assertEqual(evaluate(20.0, 10.0, st), CashoutDecision.CASHOUT)

    def test_late_goal_against_cashout(self):
        st = MatchState(minute=70, live_prob=0.5, goal_against_after_60=True)
        self.assertEqual(evaluate(20.0, 10.0, st), CashoutDecision.CASHOUT)

    def test_no_live_prob_insufficient(self):
        st = MatchState(minute=30, live_prob=None)
        self.assertEqual(evaluate(20.0, 10.0, st), CashoutDecision.INSUFFICIENTE)

    def test_high_prob_late_mantieni(self):
        st = MatchState(minute=80, live_prob=0.85)
        self.assertEqual(evaluate(20.0, 10.0, st), CashoutDecision.MANTIENI)


if __name__ == "__main__":
    unittest.main()
