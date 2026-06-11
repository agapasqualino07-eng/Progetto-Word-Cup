"""Test del raccoglitore quote storiche (funzioni pure, niente rete)."""
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.data.odds_api import MatchOdds
from src.data.odds_history import (
    append_snapshots,
    build_history,
    load_snapshots,
    results_to_outcomes,
    snapshot_rows,
    write_history_csv,
)


def _mo(mid, home, away, o1, ox, o2, ct, mock=False):
    return MatchOdds(match_id=mid, home=home, away=away, odds_1=o1, odds_x=ox,
                     odds_2=o2, source="MOCK" if mock else "the-odds-api:x",
                     commence_time=ct)


class TestSnapshot(unittest.TestCase):
    def test_snapshot_skips_mock(self):
        now = datetime(2026, 6, 12, tzinfo=timezone.utc)
        ct = now + timedelta(hours=10)
        rows = snapshot_rows([_mo("a", "Spagna", "Haiti", 1.5, 4.0, 7.0, ct),
                              _mo("m", "X", "Y", 2, 3, 4, ct, mock=True)], now)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["match_id"], "a")
        self.assertEqual(rows[0]["captured_at"], now.isoformat())

    def test_append_and_load_roundtrip(self):
        now = datetime(2026, 6, 12, tzinfo=timezone.utc)
        ct = now + timedelta(hours=5)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "snap.csv"
            append_snapshots(snapshot_rows([_mo("a", "A", "B", 1.5, 4, 7, ct)], now), p)
            append_snapshots(snapshot_rows([_mo("a", "A", "B", 1.4, 4.2, 7.5, ct)], now), p)
            snaps = load_snapshots(p)
            self.assertEqual(len(snaps), 2)


class TestResults(unittest.TestCase):
    def test_results_to_outcomes(self):
        events = [
            {"id": "a", "completed": True, "home_team": "A", "away_team": "B",
             "scores": [{"name": "A", "score": "2"}, {"name": "B", "score": "1"}]},
            {"id": "b", "completed": False, "home_team": "C", "away_team": "D",
             "scores": None},
            {"id": "c", "completed": True, "home_team": "E", "away_team": "F",
             "scores": [{"name": "E", "score": "0"}, {"name": "F", "score": "0"}]},
        ]
        out = results_to_outcomes(events)
        self.assertEqual(out, {"a": "1", "c": "X"})


class TestBuildHistory(unittest.TestCase):
    def test_opening_and_closing_selected(self):
        # Due istantanee della stessa partita: apertura=prima, chiusura=ultima
        # prima del calcio d'inizio.
        ct = "2026-06-12T20:00:00+00:00"
        snaps = [
            {"match_id": "a", "home": "Spagna", "away": "Haiti", "commence_time": ct,
             "captured_at": "2026-06-10T08:00:00+00:00",
             "odds_1": "1.50", "odds_x": "4.0", "odds_2": "7.0"},
            {"match_id": "a", "home": "Spagna", "away": "Haiti", "commence_time": ct,
             "captured_at": "2026-06-12T18:00:00+00:00",
             "odds_1": "1.40", "odds_x": "4.3", "odds_2": "8.0"},
        ]
        rows = build_history(snaps, {"a": "1"})
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["open_1"], "1.50")   # apertura
        self.assertEqual(r["close_1"], "1.40")  # chiusura
        self.assertEqual(r["actual"], "1")

    def test_match_without_result_excluded(self):
        snaps = [{"match_id": "a", "home": "A", "away": "B", "commence_time": "",
                  "captured_at": "2026-06-10T08:00:00+00:00",
                  "odds_1": "1.5", "odds_x": "4", "odds_2": "7"}]
        self.assertEqual(build_history(snaps, {}), [])

    def test_written_history_is_loadable_by_backtester(self):
        from src.backtest.history_loader import load_history_csv
        ct = "2026-06-12T20:00:00+00:00"
        snaps = [{"match_id": "a", "home": "Spagna", "away": "Haiti",
                  "commence_time": ct, "captured_at": "2026-06-10T08:00:00+00:00",
                  "odds_1": "1.5", "odds_x": "4.0", "odds_2": "7.0"}]
        rows = build_history(snaps, {"a": "1"})
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "history.csv"
            write_history_csv(rows, p)
            loaded = load_history_csv(p)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].actual, "1")


if __name__ == "__main__":
    unittest.main()
