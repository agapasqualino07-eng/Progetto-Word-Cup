"""Test del loader di dati storici reali (validazione + integrazione backtester)."""
import os
import tempfile
import unittest
from pathlib import Path

from src.backtest.backtester import Backtester
from src.backtest.history_loader import (
    HistoryLoadError,
    load_history_csv,
    load_real_history,
    parse_history_csv,
)

VALID_CSV = """\
# commento iniziale da ignorare
home,away,actual,open_1,open_x,open_2,close_1,close_x,close_2
Francia,Marocco,1,1.70,3.60,5.00,1.62,3.70,5.40

# riga vuota sopra e commento qui: entrambi ignorati
Brasile,Svizzera,2,1.55,3.90,6.50,1.50,4.00,7.00
"""


class TestParseHistory(unittest.TestCase):
    def test_parses_valid_rows_and_skips_comments(self):
        matches = parse_history_csv(VALID_CSV)
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0].home, "Francia")
        self.assertEqual(matches[0].actual, "1")
        self.assertEqual(matches[1].actual, "2")
        self.assertEqual(matches[0].open_1, 1.70)

    def test_lowercase_outcome_is_normalised(self):
        csv = (
            "home,away,actual,open_1,open_x,open_2,close_1,close_x,close_2\n"
            "A,B,x,2.0,3.0,4.0,2.0,3.0,4.0\n"
        )
        self.assertEqual(parse_history_csv(csv)[0].actual, "X")

    def test_invalid_outcome_rejected(self):
        bad = (
            "home,away,actual,open_1,open_x,open_2,close_1,close_x,close_2\n"
            "A,B,3,2.0,3.0,4.0,2.0,3.0,4.0\n"
        )
        with self.assertRaises(HistoryLoadError):
            parse_history_csv(bad)

    def test_odds_must_be_above_one(self):
        bad = (
            "home,away,actual,open_1,open_x,open_2,close_1,close_x,close_2\n"
            "A,B,1,1.00,3.0,4.0,2.0,3.0,4.0\n"
        )
        with self.assertRaises(HistoryLoadError):
            parse_history_csv(bad)

    def test_non_numeric_odds_rejected(self):
        bad = (
            "home,away,actual,open_1,open_x,open_2,close_1,close_x,close_2\n"
            "A,B,1,abc,3.0,4.0,2.0,3.0,4.0\n"
        )
        with self.assertRaises(HistoryLoadError):
            parse_history_csv(bad)

    def test_missing_column_rejected(self):
        bad = "home,away,actual,open_1,open_x,open_2,close_1,close_x\nA,B,1,2,3,4,2,3\n"
        with self.assertRaises(HistoryLoadError):
            parse_history_csv(bad)

    def test_empty_file_rejected(self):
        with self.assertRaises(HistoryLoadError):
            parse_history_csv("# solo commenti\n\n")


class TestLoadFromDisk(unittest.TestCase):
    def test_missing_file_raises(self):
        with self.assertRaises(HistoryLoadError):
            load_history_csv("/percorso/inesistente/history.csv")

    def test_load_real_history_returns_none_when_absent(self):
        # Percorso esplicito inesistente -> None (niente dati finti).
        self.assertIsNone(load_real_history("/percorso/inesistente/history.csv"))

    def test_roundtrip_file_and_backtest(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "history.csv"
            path.write_text(VALID_CSV, encoding="utf-8")
            matches = load_history_csv(path)
            self.assertEqual(len(matches), 2)
            # Il backtester accetta i dati caricati e produce metriche coerenti.
            res = Backtester().run(matches)
            self.assertEqual(res.n_matches, 2)
            self.assertLessEqual(res.n_bets, res.n_matches)

    def test_env_var_path_is_used(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "h.csv"
            path.write_text(VALID_CSV, encoding="utf-8")
            os.environ["WCE_HISTORY_CSV"] = str(path)
            try:
                matches = load_real_history()
                self.assertIsNotNone(matches)
                self.assertEqual(len(matches), 2)
            finally:
                del os.environ["WCE_HISTORY_CSV"]


if __name__ == "__main__":
    unittest.main()
