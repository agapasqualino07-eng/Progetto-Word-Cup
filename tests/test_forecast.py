"""Test dei pronostici di giornata (un esito per ogni partita)."""
import unittest
from datetime import datetime, timedelta, timezone

from src.data.odds_api import MatchOdds, mock_matchday
from src.ml.ratings_loader import load_ratings_model
from src.services.forecast import (
    Forecast,
    build_forecasts,
    format_forecasts,
    most_likely_score,
)


def _m(mid, home, away, o1, ox, o2, hrs):
    ct = datetime.now(timezone.utc) + timedelta(hours=hrs)
    return MatchOdds(match_id=mid, home=home, away=away, odds_1=o1, odds_x=ox,
                     odds_2=o2, source="the-odds-api:x", commence_time=ct)


class TestMostLikelyScore(unittest.TestCase):
    def test_score_consistent_with_outcome(self):
        sh, sa = most_likely_score(2.1, 0.6, "1")
        self.assertGreater(sh, sa)                 # esito 1 → casa segna di più
        self.assertEqual(most_likely_score(1.0, 1.0, "X")[0],
                         most_likely_score(1.0, 1.0, "X")[1])  # X → pari


class TestBuildForecasts(unittest.TestCase):
    def test_one_forecast_per_match_sorted(self):
        matches = [_m("b", "Brasile", "Haiti", 1.5, 4.0, 7.0, 20),
                   _m("a", "Spagna", "Capo Verde", 1.3, 5.0, 9.0, 5)]
        fc = build_forecasts(matches)
        self.assertEqual(len(fc), 2)
        # ordinate per orario: prima la partita tra 5h.
        self.assertEqual(fc[0].home, "Spagna")
        for f in fc:
            self.assertIn(f.outcome, {"1", "X", "2"})
            self.assertTrue(0.0 <= f.prob <= 1.0)

    def test_favourite_predicted_with_ratings(self):
        model = load_ratings_model()
        if model is None:
            self.skipTest("file rating assente")
        fc = build_forecasts([_m("a", "Spagna", "Capo Verde", 1.3, 5.0, 9.0, 5)], model)
        self.assertEqual(fc[0].outcome, "1")       # Spagna nettamente favorita
        self.assertGreater(fc[0].prob, 0.5)

    def test_format_contains_matches_and_caveat(self):
        fc = build_forecasts(mock_matchday())
        text = format_forecasts(fc)
        self.assertIn("PRONOSTICI", text)
        self.assertIn("non una certezza", text)

    def test_empty(self):
        self.assertEqual(format_forecasts([]), "")


if __name__ == "__main__":
    unittest.main()
