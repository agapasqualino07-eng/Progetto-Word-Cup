"""Test delle metriche 'spremitura test': schedina giornaliera + calibrazione + data."""
import unittest

from src.backtest.history_loader import parse_history_csv
from src.backtest.sample_data import HistoricalMatch
from src.services.performance import (
    MatchPred,
    calibration_table,
    schedina_record,
)


def _hm(date, home, away, actual, o1, ox, o2):
    return HistoricalMatch(home, away, actual, o1, ox, o2, o1, ox, o2, date=date)


class TestDateColumn(unittest.TestCase):
    def test_loader_reads_optional_date(self):
        csv = ("date,home,away,actual,open_1,open_x,open_2,close_1,close_x,close_2\n"
               "2026-06-20,Brasile,Haiti,1,1.1,9,20,1.1,9,20\n")
        m = parse_history_csv(csv)[0]
        self.assertEqual(m.date, "2026-06-20")

    def test_loader_without_date_defaults_empty(self):
        csv = ("home,away,actual,open_1,open_x,open_2,close_1,close_x,close_2\n"
               "Brasile,Haiti,1,1.1,9,20,1.1,9,20\n")
        self.assertEqual(parse_history_csv(csv)[0].date, "")


def _pred(date, prob, win, oo=2.0):
    return MatchPred(date=date, pronostico="1", prob=prob, win=win,
                     open_odds=oo, close_odds=oo)


class TestSchedina(unittest.TestCase):
    def test_winning_day_pays_combined(self):
        # Un giorno con 2 gambe vincenti a quota 2.0 → vincita 10*(4-1)=30.
        preds = [_pred("2026-06-20", 0.7, True, 2.0),
                 _pred("2026-06-20", 0.6, True, 2.0)]
        rec = schedina_record(preds)
        self.assertEqual(rec.n_days, 1)
        self.assertEqual(rec.won, 1)
        self.assertAlmostEqual(rec.profit, 30.0)

    def test_losing_leg_loses_stake(self):
        preds = [_pred("2026-06-20", 0.7, True), _pred("2026-06-20", 0.6, False)]
        rec = schedina_record(preds)
        self.assertEqual(rec.won, 0)
        self.assertAlmostEqual(rec.profit, -10.0)

    def test_single_match_day_skipped(self):
        # Un solo match in un giorno: niente multipla.
        self.assertEqual(schedina_record([_pred("2026-06-20", 0.9, True)]).n_days, 0)

    def test_picks_most_probable_legs(self):
        preds = [_pred("d", 0.9, True), _pred("d", 0.8, True), _pred("d", 0.5, False)]
        # top-3 include la gamba persa → schedina persa
        self.assertEqual(schedina_record(preds, size=3).won, 0)
        # top-2 = solo le due più probabili → vinta
        self.assertEqual(schedina_record(preds, size=2).won, 1)


class TestCalibration(unittest.TestCase):
    def test_bands_report_predicted_vs_actual(self):
        preds = [_pred("d", 0.60, True), _pred("d", 0.62, False),
                 _pred("d", 0.61, True)]
        table = calibration_table(preds)
        # tutte e tre nella fascia 55-70
        self.assertEqual(len(table), 1)
        label, n, avg_p, hit = table[0]
        self.assertEqual(n, 3)
        self.assertAlmostEqual(hit, 2 / 3, places=6)


if __name__ == "__main__":
    unittest.main()
