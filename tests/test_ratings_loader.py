"""Test del loader rating reali e dell'iniezione nel modello Poisson."""
import tempfile
import unittest
from pathlib import Path

from src.ml.poisson_model import PoissonModel
from src.ml.ratings_loader import (
    RatingsLoadError,
    build_model_from_ratings,
    load_ratings_model,
    parse_ratings_csv,
    ratings_to_attack_defense,
)

VALID = """\
# rating di esempio (scala arbitraria ma coerente)
team,rating
Brasile,2000
Haiti,1300
Spagna,1950
# riga vuota sotto e squadra non compilata (ignorata)
Scozia,
"""


class TestParseRatings(unittest.TestCase):
    def test_parses_and_skips_blank_rating(self):
        r = parse_ratings_csv(VALID)
        self.assertEqual(set(r), {"Brasile", "Haiti", "Spagna"})
        self.assertEqual(r["Brasile"], 2000.0)

    def test_missing_column_rejected(self):
        with self.assertRaises(RatingsLoadError):
            parse_ratings_csv("team\nBrasile\n")

    def test_non_numeric_rating_rejected(self):
        with self.assertRaises(RatingsLoadError):
            parse_ratings_csv("team,rating\nBrasile,fortissimo\n")

    def test_needs_at_least_two(self):
        with self.assertRaises(RatingsLoadError):
            parse_ratings_csv("team,rating\nBrasile,2000\n")


class TestMapping(unittest.TestCase):
    def test_stronger_team_has_more_attack_and_better_defense(self):
        ratings = {"Forte": 2000, "Media": 1600, "Debole": 1200}
        attack, defense = ratings_to_attack_defense(ratings)
        # Più rating → più attacco.
        self.assertGreater(attack["Forte"], attack["Media"])
        self.assertGreater(attack["Media"], attack["Debole"])
        # Più rating → difesa più NEGATIVA (più forte).
        self.assertLess(defense["Forte"], defense["Media"])
        self.assertLess(defense["Media"], defense["Debole"])

    def test_model_uses_injected_ratings_over_tiers(self):
        # Diamo a una squadra "debole" (Haiti) un rating altissimo: il modello
        # deve usare il rating iniettato, non la fascia di constants.
        ratings = {"Haiti": 2100, "Brasile": 1300}
        model = build_model_from_ratings(ratings)
        base = PoissonModel()
        self.assertGreater(model._attack("Haiti"), base._attack("Haiti"))
        self.assertLess(model._attack("Brasile"), base._attack("Brasile"))


class TestLoadFromDisk(unittest.TestCase):
    def test_absent_file_returns_none(self):
        self.assertIsNone(load_ratings_model("/percorso/inesistente/ratings.csv"))

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "team_ratings.csv"
            p.write_text(VALID, encoding="utf-8")
            model = load_ratings_model(p)
            self.assertIsInstance(model, PoissonModel)
            self.assertIn("Brasile", model.attack)


class TestCommittedRatings(unittest.TestCase):
    """Protegge il file rating reale committato (data/team_ratings.csv)."""

    def test_committed_file_loads_with_48_wc_teams(self):
        from src.constants import GROUPS

        path = Path("data/team_ratings.csv")
        if not path.exists():
            self.skipTest("file rating committato assente")
        model = load_ratings_model(path)
        self.assertIsNotNone(model)
        wc_teams = [t for g in GROUPS.values() for t in g]
        for team in wc_teams:
            self.assertIn(team, model.attack, f"rating mancante per {team}")


if __name__ == "__main__":
    unittest.main()
