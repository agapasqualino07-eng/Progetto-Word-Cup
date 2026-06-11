"""Test dell'allocatore 4-4-2 e dei vincoli di correlazione."""
import unittest
from datetime import date

from src.betting.daily_allocator import (
    ALLOCATION_BY_MATCHES,
    DailyAllocator,
    get_daily_plan_params,
)
from src.betting.correlation_matrix import correlation, is_forbidden_pair
from src.models.schemas import Outcome, Phase, Selection


def make_selection(i, group="A", matchday=1, edge_target=0.12, day=1):
    """Crea una selezione con edge ~edge_target (quota 2.0 → implicita 0.5)."""
    return Selection(
        match_id=f"m{i}",
        home=f"Casa{i}",
        away=f"Ospite{i}",
        outcome=Outcome.HOME,
        model_prob=0.5 + edge_target,
        odds=2.0,
        group=group,
        matchday=matchday,
        kickoff_date=date(2026, 6, day),
        phase=Phase.GROUP,
    )


class TestAllocationParams(unittest.TestCase):
    def test_full_plan_is_442(self):
        p = ALLOCATION_BY_MATCHES[4]
        self.assertEqual((p["singole"], p["doppie"], p["triple"]), (4, 4, 2))

    def test_budget_pct_scales_with_matches(self):
        self.assertEqual(get_daily_plan_params(1, 100)["budget"], 10.0)
        self.assertEqual(get_daily_plan_params(2, 100)["budget"], 30.0)
        self.assertEqual(get_daily_plan_params(3, 100)["budget"], 60.0)
        self.assertEqual(get_daily_plan_params(4, 100)["budget"], 100.0)

    def test_stake_is_clamped(self):
        # Bankroll enorme → stake limitato dal cap (20).
        self.assertEqual(get_daily_plan_params(4, 10000)["stake"], 20.0)
        # Bankroll piccolo → stake limitato dal floor (5).
        self.assertEqual(get_daily_plan_params(4, 50)["stake"], 5.0)


class TestCorrelation(unittest.TestCase):
    def test_same_group_matchday3_forbidden(self):
        a = make_selection(1, group="A", matchday=3)
        b = make_selection(2, group="A", matchday=3)
        self.assertTrue(is_forbidden_pair(a, b))
        self.assertGreaterEqual(correlation(a, b), 0.95)

    def test_different_groups_independent(self):
        a = make_selection(1, group="A")
        b = make_selection(2, group="B")
        self.assertEqual(correlation(a, b), 0.0)

    def test_same_match_fully_correlated(self):
        a = make_selection(1)
        b = make_selection(1)
        self.assertEqual(correlation(a, b), 1.0)


class TestAllocator(unittest.TestCase):
    def test_full_day_produces_442(self):
        # 6 partite in gironi diversi, tutte con valore → piano 4-4-2 pieno.
        sels = [
            make_selection(i, group=g, matchday=1, day=i)
            for i, g in enumerate("ABCDEF", start=1)
        ]
        plan = DailyAllocator().allocate(sels, date(2026, 6, 20), 100.0)
        self.assertEqual(len(plan.singole), 4)
        self.assertEqual(len(plan.doppie), 4)
        self.assertEqual(len(plan.triple), 2)

    def test_no_value_no_bets(self):
        # Tutte senza edge → nessuna bet (anti "bet su tutto").
        sels = [make_selection(i, group=g, edge_target=-0.05, day=i)
                for i, g in enumerate("ABCD", start=1)]
        plan = DailyAllocator().allocate(sels, date(2026, 6, 20), 100.0)
        self.assertEqual(len(plan.all_bets), 0)

    def test_combos_never_use_forbidden_pairs(self):
        # Due match stesso girone 3ª giornata: non devono finire nella stessa combo.
        sels = [
            make_selection(1, group="A", matchday=3, day=27),
            make_selection(2, group="A", matchday=3, day=27),
            make_selection(3, group="B", matchday=1, day=20),
            make_selection(4, group="C", matchday=1, day=20),
            make_selection(5, group="D", matchday=1, day=20),
        ]
        plan = DailyAllocator().allocate(sels, date(2026, 6, 27), 100.0)
        for bet in plan.doppie + plan.triple:
            ids = {leg.match_id for leg in bet.legs}
            self.assertFalse({"m1", "m2"}.issubset(ids))


if __name__ == "__main__":
    unittest.main()
