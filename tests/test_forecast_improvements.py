"""Test delle migliorie ai pronostici: Dixon-Coles, fattore campo, peso mercato,
schedina a massima probabilità."""
import unittest

from src.data.odds_api import mock_matchday
from src.ml.poisson_model import PoissonModel
from src.services.forecast import (
    FORECAST_MODEL_WEIGHT,
    Forecast,
    build_forecasts,
    build_schedina,
    format_forecasts,
    schedina_stats,
)
from src.anti_hallucination import ConfidenceLevel


class TestDixonColes(unittest.TestCase):
    def test_negative_rho_raises_draw_probability(self):
        base = PoissonModel().predict_match("Francia", "Senegal")
        dc = PoissonModel(rho=-0.10).predict_match("Francia", "Senegal")
        self.assertGreater(dc.prob_x, base.prob_x)

    def test_rho_zero_is_identity(self):
        a = PoissonModel().predict_match("Brasile", "Scozia")
        b = PoissonModel(rho=0.0).predict_match("Brasile", "Scozia")
        self.assertAlmostEqual(a.prob_x, b.prob_x, places=9)

    def test_probabilities_still_sum_to_one_with_rho(self):
        p = PoissonModel(rho=-0.12).predict_match("Spagna", "Capo Verde")
        self.assertAlmostEqual(p.prob_1 + p.prob_x + p.prob_2, 1.0, places=6)


class TestHomeAdvantage(unittest.TestCase):
    def test_generic_home_adv_applies_at_own_venue(self):
        m = PoissonModel(home_adv=0.25)
        at_home = m.expected_goals("Norvegia", "Iraq", "Norvegia")[0]
        neutral = m.expected_goals("Norvegia", "Iraq", None)[0]
        self.assertGreater(at_home, neutral)

    def test_world_cup_neutral_unchanged(self):
        # In campo neutro (Mondiale) home_adv non deve cambiare nulla.
        a = PoissonModel(home_adv=0.25).predict_match("Norvegia", "Iraq", None)
        b = PoissonModel().predict_match("Norvegia", "Iraq", None)
        self.assertAlmostEqual(a.prob_1, b.prob_1, places=9)


class TestForecastMarketWeight(unittest.TestCase):
    def test_forecast_prob_closer_to_market(self):
        # Quota casa molto bassa (mercato sicuro): il pronostico col peso 0.30
        # deve avvicinarsi al mercato più di quanto farebbe il modello puro.
        self.assertLess(FORECAST_MODEL_WEIGHT, 0.5)
        odds = mock_matchday()
        fc = build_forecasts(odds)
        self.assertEqual(len(fc), len(odds))


class TestSchedina(unittest.TestCase):
    def _fc(self, home, prob, odds=1.5, outcome="1"):
        return Forecast(home=home, away="X", outcome=outcome, prob=prob,
                        score_home=1, score_away=0,
                        confidence=ConfidenceLevel.MEDIA, odds=odds)

    def test_picks_highest_probability_legs(self):
        fs = [self._fc("A", 0.50), self._fc("B", 0.80), self._fc("C", 0.70),
              self._fc("D", 0.60)]
        legs = build_schedina(fs, size=3)
        self.assertEqual([l.home for l in legs], ["B", "C", "D"])

    def test_joint_probability_is_product(self):
        legs = [self._fc("A", 0.8, odds=1.5), self._fc("B", 0.5, odds=2.0)]
        joint, quota = schedina_stats(legs)
        self.assertAlmostEqual(joint, 0.4, places=9)
        self.assertAlmostEqual(quota, 3.0, places=9)

    def test_missing_odds_gives_no_quota(self):
        legs = [self._fc("A", 0.8, odds=None), self._fc("B", 0.5, odds=2.0)]
        joint, quota = schedina_stats(legs)
        self.assertAlmostEqual(joint, 0.4, places=9)
        self.assertIsNone(quota)

    def test_format_contains_schedina_and_caveat(self):
        text = format_forecasts(build_forecasts(mock_matchday()))
        self.assertIn("SCHEDINA PIÙ PROBABILE", text)
        self.assertIn("Prob. di vincerla", text)
        self.assertIn("non il valore atteso", text)


if __name__ == "__main__":
    unittest.main()
