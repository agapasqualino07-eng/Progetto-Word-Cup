"""Test della normalizzazione nomi squadre (fonti EN → nomi canonici IT).

Bug coperto: i dati REALI di The Odds API arrivano coi nomi inglesi
("South Korea", "Bosnia & Herzegovina"...) e senza normalizzazione i lookup di
rating/gironi/correlazioni falliscono in silenzio.
"""
import unittest

from src.constants import group_of
from src.data.odds_api import OddsCollector
from src.data.odds_history import build_history
from src.data.team_names import CANONICAL, is_known_team, normalize_team
from src.ml.ratings_loader import load_ratings_model


class TestNormalize(unittest.TestCase):
    def test_known_aliases(self):
        cases = {
            "South Korea": "Corea del Sud",
            "Korea Republic": "Corea del Sud",
            "Czech Republic": "Cechia",
            "Czechia": "Cechia",
            "Bosnia & Herzegovina": "Bosnia-Erzegovina",
            "Bosnia and Herzegovina": "Bosnia-Erzegovina",
            "Türkiye": "Turchia",
            "Ivory Coast": "Costa d'Avorio",
            "Cape Verde": "Capo Verde",
            "United States": "USA",
            "IR Iran": "Iran",
            "New Zealand": "Nuova Zelanda",
        }
        for alias, expected in cases.items():
            self.assertEqual(normalize_team(alias), expected, alias)

    def test_canonical_names_unchanged(self):
        for name in ("Spagna", "Corea del Sud", "Bosnia-Erzegovina", "USA"):
            self.assertEqual(normalize_team(name), name)

    def test_unknown_passthrough_never_invented(self):
        self.assertEqual(normalize_team("Atlantide"), "Atlantide")
        self.assertFalse(is_known_team("Atlantide"))

    def test_all_aliases_point_to_canonical(self):
        from src.data.team_names import ALIASES
        for alias, target in ALIASES.items():
            self.assertIn(target, CANONICAL, f"alias {alias} → {target} non canonico")


class TestParseEventNormalises(unittest.TestCase):
    def test_api_event_gets_italian_names_and_group(self):
        ev = {
            "id": "x1", "home_team": "South Korea", "away_team": "Czech Republic",
            "commence_time": "2026-06-12T02:00:00Z",
            "bookmakers": [{"key": "b", "markets": [{"key": "h2h", "outcomes": [
                {"name": "South Korea", "price": 2.69},
                {"name": "Czech Republic", "price": 3.06},
                {"name": "Draw", "price": 3.1},
            ]}]}],
        }
        m = OddsCollector._parse_event(ev)
        self.assertEqual(m.home, "Corea del Sud")
        self.assertEqual(m.away, "Cechia")
        self.assertEqual(m.group, group_of("Corea del Sud"))  # girone risolto

    def test_normalised_names_find_fifa_ratings(self):
        model = load_ratings_model()
        if model is None:
            self.skipTest("file rating assente")
        # Dopo la normalizzazione, i nomi API trovano il rating FIFA.
        for api_name in ("South Korea", "Bosnia & Herzegovina", "Czech Republic"):
            self.assertIn(normalize_team(api_name), model.attack)


class TestHistoryNormalises(unittest.TestCase):
    def test_old_english_snapshots_normalised_in_history(self):
        snaps = [{"match_id": "a", "home": "South Korea", "away": "Czech Republic",
                  "commence_time": "", "captured_at": "2026-06-10T08:00:00+00:00",
                  "odds_1": "2.7", "odds_x": "3.1", "odds_2": "3.0"}]
        rows = build_history(snaps, {"a": "1"})
        self.assertEqual(rows[0]["home"], "Corea del Sud")
        self.assertEqual(rows[0]["away"], "Cechia")


if __name__ == "__main__":
    unittest.main()
