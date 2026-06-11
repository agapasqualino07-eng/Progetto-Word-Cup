"""Test della pipeline odds→modello→piano e del collector quote."""
import unittest
from datetime import date

from src.data.odds_api import OddsCollector, mock_matchday
from src.services.pipeline import build_selections, generate_plan
from src.services.serializers import plan_to_dict


class TestOddsCollector(unittest.TestCase):
    def test_mock_has_matches(self):
        odds = OddsCollector().get_odds(use_mock=True)
        self.assertGreaterEqual(len(odds), 4)
        self.assertTrue(all(o.is_mock for o in odds))

    def test_mock_groups_resolved(self):
        # I gironi vengono risolti dalle costanti.
        odds = mock_matchday()
        francia = next(o for o in odds if o.home == "Francia")
        self.assertEqual(francia.group, "I")

    def test_no_key_no_api(self):
        # Senza chiave, use_mock=False deve fallire (niente quote inventate).
        with self.assertRaises(RuntimeError):
            OddsCollector(api_key="").get_odds(use_mock=False)


class TestPipeline(unittest.TestCase):
    def test_build_selections_one_per_match(self):
        odds = mock_matchday()
        sels = build_selections(odds)
        self.assertEqual(len(sels), len(odds))
        # match_id univoci.
        self.assertEqual(len({s.match_id for s in sels}), len(odds))

    def test_generate_plan_is_serializable(self):
        odds = mock_matchday()
        plan = generate_plan(odds, bankroll=120.0, plan_date=date(2026, 6, 16))
        d = plan_to_dict(plan)
        self.assertEqual(d["bankroll"], 120.0)
        self.assertIn("singole", d)
        self.assertIsInstance(d["n_bet"], int)


if __name__ == "__main__":
    unittest.main()
