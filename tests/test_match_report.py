"""Test del report on-demand per singola partita."""
import unittest

from src.services.match_report import build_match_report


class TestMatchReport(unittest.TestCase):
    def test_report_without_odds_has_prediction_no_advice(self):
        r = build_match_report("Argentina", "Messico")
        self.assertIn(r.pronostico, {"1", "X", "2"})
        self.assertFalse(r.has_odds)
        self.assertIsNone(r.consiglio)
        self.assertIn("VERIFICA SU SNAI", r.to_text())

    def test_probabilities_sum_to_one(self):
        r = build_match_report("Brasile", "Scozia")
        self.assertAlmostEqual(r.prob_1 + r.prob_x + r.prob_2, 1.0, places=6)

    def test_favorite_predicted(self):
        # Argentina (tier1) vs Curaçao (tier4): pronostico = 1.
        r = build_match_report("Argentina", "Curaçao")
        self.assertEqual(r.pronostico, "1")

    def test_with_odds_gives_advice(self):
        # Quota generosa sulla favorita → consiglio SCOMMETTI.
        r = build_match_report("Argentina", "Curaçao",
                               odds={"1": 1.9, "X": 4.0, "2": 7.0})
        self.assertTrue(r.has_odds)
        self.assertIn(r.consiglio, {"SCOMMETTI", "NON SCOMMETTERE"})
        self.assertIsNotNone(r.edge)

    def test_efficient_odds_no_bet(self):
        # Quota strettissima sulla favorita → nessun valore → NON SCOMMETTERE.
        r = build_match_report("Argentina", "Curaçao",
                               odds={"1": 1.05, "X": 9.0, "2": 21.0})
        self.assertEqual(r.consiglio, "NON SCOMMETTERE")

    def test_dict_serializable(self):
        d = build_match_report("Francia", "Senegal",
                               odds={"1": 1.7, "X": 3.8, "2": 5.0}).to_dict()
        self.assertIn("probabilita", d)
        self.assertIn("scommessa", d)
        self.assertIsNotNone(d["scommessa"])

    def test_host_note_present(self):
        r = build_match_report("USA", "Paraguay", venue_country="USA")
        self.assertTrue(any("casa" in n for n in r.notes))


if __name__ == "__main__":
    unittest.main()
