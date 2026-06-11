"""Test del filtro temporale e del parsing orari (dati reali Odds API)."""
import unittest
from datetime import datetime, timedelta, timezone

from src.data.odds_api import (
    MatchOdds,
    OddsCollector,
    _parse_iso,
    filter_upcoming,
)
from src.notifications.message_formatter import format_daily_plan
from src.data.odds_api import mock_matchday
from src.services.pipeline import generate_plan
from datetime import date


def _m(name: str, hours_from_now: float | None) -> MatchOdds:
    ct = None
    if hours_from_now is not None:
        ct = datetime.now(timezone.utc) + timedelta(hours=hours_from_now)
    return MatchOdds(
        match_id=name, home=name, away="X",
        odds_1=2.0, odds_x=3.0, odds_2=4.0,
        source="the-odds-api:test", commence_time=ct,
    )


class TestParseIso(unittest.TestCase):
    def test_parses_z_suffix_as_utc(self):
        dt = _parse_iso("2026-06-12T18:00:00Z")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.tzinfo, timezone.utc)
        self.assertEqual(dt.hour, 18)

    def test_invalid_returns_none(self):
        self.assertIsNone(_parse_iso("non-una-data"))
        self.assertIsNone(_parse_iso(None))


class TestFilterUpcoming(unittest.TestCase):
    def test_keeps_only_matches_in_window(self):
        matches = [
            _m("tra_2h", 2),       # dentro
            _m("tra_28h", 28),     # dentro (finestra 30h)
            _m("tra_40h", 40),     # fuori
            _m("gia_giocata", -5), # passata
            _m("senza_ora", None), # nessun orario → esclusa
        ]
        kept = filter_upcoming(matches, within_hours=30)
        names = {m.match_id for m in kept}
        self.assertEqual(names, {"tra_2h", "tra_28h"})

    def test_none_window_disables_filter(self):
        matches = [_m("a", 100), _m("b", None)]
        self.assertEqual(len(filter_upcoming(matches, within_hours=None)), 2)

    def test_mock_is_not_filtered(self):
        # Senza chiave → mock, restituito intero (deterministico per demo/test).
        odds = OddsCollector().get_odds(use_mock=True)
        self.assertGreaterEqual(len(odds), 4)


class TestMockBanner(unittest.TestCase):
    def test_mock_banner_present(self):
        plan = generate_plan(mock_matchday(), 100.0, date(2026, 6, 16))
        text = format_daily_plan(plan, 1000.0, is_mock=True)
        self.assertIn("DATI DI ESEMPIO", text)
        self.assertIn("ODDS_API_KEY", text)

    def test_no_banner_when_real(self):
        plan = generate_plan(mock_matchday(), 100.0, date(2026, 6, 16))
        text = format_daily_plan(plan, 1000.0, is_mock=False)
        self.assertNotIn("DATI DI ESEMPIO", text)

    def test_no_matches_message(self):
        plan = generate_plan([], 100.0, date(2026, 6, 16))
        text = format_daily_plan(plan, 1000.0, is_mock=False, n_matches=0)
        self.assertIn("Nessuna partita in programma", text)

    def test_skipped_matches_shown_with_reason(self):
        # Il mock contiene partite senza valore: devono comparire come "saltate".
        plan = generate_plan(mock_matchday(), 100.0, date(2026, 6, 16))
        self.assertTrue(plan.skipped, "ci si aspetta partite scartate nel mock")
        text = format_daily_plan(plan, 1000.0)
        self.assertIn("Altre partite di oggi", text)
        self.assertIn("nessun valore", text)


if __name__ == "__main__":
    unittest.main()
