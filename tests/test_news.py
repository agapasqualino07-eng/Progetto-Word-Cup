"""Test del news engine: sentiment, impatto, feature, integrazione nel report."""
import unittest

from src.data.news.collector import NewsCollector, NewsItem, _parse_rss, mock_news
from src.data.news.sentiment import analyze
from src.features.news_features import (
    has_injury_news,
    injury_impact,
    morale_delta,
    team_sentiment,
)
from src.services.match_report import build_match_report


def _item(title, summary=""):
    return NewsItem("Test", title, "https://x/y", "2026-06-10", summary)


class TestSentiment(unittest.TestCase):
    def test_injury_is_negative_and_flagged(self):
        s = analyze("Infortunio per il titolare, salta la partita")
        self.assertLess(s.score, 0)
        self.assertTrue(s.injury_flag)

    def test_positive_recovery(self):
        s = analyze("Recuperato il titolare, torna in forma")
        self.assertGreater(s.score, 0)
        self.assertFalse(s.injury_flag)

    def test_neutral_zero(self):
        s = analyze("Conferenza stampa del commissario tecnico")
        self.assertEqual(s.score, 0.0)


class TestFeatures(unittest.TestCase):
    def test_team_sentiment_average(self):
        items = [_item("torna titolare recuperato"), _item("infortunio out")]
        # uno positivo, uno negativo → media vicina a 0
        self.assertAlmostEqual(team_sentiment(items), 0.0, places=3)

    def test_injury_impact_and_flag(self):
        items = [_item("infortunio, salta"), _item("conferenza stampa")]
        self.assertEqual(injury_impact(items), 0.5)
        self.assertTrue(has_injury_news(items))

    def test_morale_delta_sign(self):
        home = [_item("vittoria, fiducia, torna la stella")]
        away = [_item("crisi, infortunio, eliminazione")]
        self.assertGreater(morale_delta(home, away), 0)

    def test_empty_news_zero(self):
        self.assertEqual(team_sentiment([]), 0.0)
        self.assertEqual(injury_impact([]), 0.0)


class TestCollector(unittest.TestCase):
    def test_parse_rss(self):
        xml = b"""<rss><channel>
          <item><title>Italia, problema</title><link>http://a/b</link>
          <pubDate>Wed, 10 Jun 2026</pubDate><description>desc</description></item>
        </channel></rss>"""
        items = _parse_rss(xml, "Fonte")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].source, "Fonte")
        self.assertEqual(items[0].url, "http://a/b")

    def test_mock_is_labeled(self):
        items = mock_news("Italia")
        self.assertTrue(all(i.is_mock for i in items))

    def test_for_team_mock(self):
        items = NewsCollector().for_team("Brasile", use_mock=True)
        self.assertTrue(items and all("Brasile" in i.title for i in items))


class TestReportWithNews(unittest.TestCase):
    def test_news_notes_in_report(self):
        nh = [_item("Argentina, infortunio per un big, salta")]
        na = [_item("Messico carico, recuperato un titolare")]
        r = build_match_report("Argentina", "Messico", news_home=nh, news_away=na)
        text = r.to_text()
        self.assertTrue(any("🗞️" in n for n in r.notes))
        self.assertIsNotNone(r.news_morale_delta)

    def test_offline_news_reports_missing(self):
        # news richieste ma vuote (offline) → nota "DATO MANCANTE", non inventa
        r = build_match_report("Francia", "Senegal", news_home=[], news_away=[])
        self.assertTrue(any("DATO MANCANTE" in n for n in r.notes))

    def test_injury_news_reduces_confidence(self):
        # Infortunio nella squadra favorita su cui si scommetterebbe → confidenza giù
        odds = {"1": 1.7, "X": 4.5, "2": 7.5}
        nh = [_item("Spagna, infortunio grave, salta il match")]
        r_inj = build_match_report("Spagna", "Capo Verde", odds=odds, news_home=nh)
        r_ok = build_match_report("Spagna", "Capo Verde", odds=odds, news_home=[])
        # con infortunio la nota di confidenza ridotta deve comparire
        self.assertTrue(any("confidenza è ridotta" in n.lower() for n in r_inj.notes))


if __name__ == "__main__":
    unittest.main()
