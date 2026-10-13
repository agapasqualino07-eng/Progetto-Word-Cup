import unittest
from decimal import Decimal

from dropship.config import PricingConfig, TrendThresholds
from dropship.models import MISSING, TrendSignal
from dropship.orders.suppliers import MockSupplier
from dropship.trends.scoring import rank, score_candidate
from dropship.trends.service import scan
from dropship.trends.sources import MockTrendSource, SerpApiTrendSource
from tests.helpers import FakeTransport, make_candidate

TH = TrendThresholds()
PC = PricingConfig()


def signal(**kw):
    data = dict(sku="SKU-1", demand_growth=0.8, ad_saturation=0.2, seasonality=0.7, source="MOCK")
    data.update(kw)
    return TrendSignal(**data)


class TestScoring(unittest.TestCase):
    def test_strong_product_passes(self):
        r = score_candidate(make_candidate(), signal(), TH, PC)
        self.assertTrue(r.passed, r.reasons)
        self.assertGreaterEqual(r.score, TH.min_score)
        self.assertLessEqual(r.score, 100)

    def test_low_growth_fails_threshold(self):
        r = score_candidate(make_candidate(), signal(demand_growth=0.05), TH, PC)
        self.assertFalse(r.passed)
        self.assertTrue(any("crescita" in x for x in r.reasons))

    def test_saturated_ads_fail_threshold(self):
        r = score_candidate(make_candidate(), signal(ad_saturation=0.9), TH, PC)
        self.assertFalse(r.passed)
        self.assertTrue(any("saturazione" in x for x in r.reasons))

    def test_heavy_product_fails_threshold(self):
        r = score_candidate(make_candidate(weight_kg=5.0), signal(), TH, PC)
        self.assertFalse(r.passed)
        self.assertTrue(any("peso" in x for x in r.reasons))

    def test_low_margin_fails_threshold(self):
        c = make_candidate(supplier_cost=Decimal("25"), market_price=Decimal("39.90"))
        r = score_candidate(c, signal(), TH, PC)
        self.assertFalse(r.passed)
        self.assertTrue(any("margine" in x for x in r.reasons))

    def test_missing_growth_is_never_invented(self):
        r = score_candidate(make_candidate(), signal(demand_growth=None), TH, PC)
        self.assertFalse(r.passed)
        self.assertTrue(any(MISSING in x for x in r.reasons))

    def test_missing_market_price_means_missing_margin(self):
        r = score_candidate(make_candidate(market_price=None), signal(), TH, PC)
        self.assertFalse(r.passed)
        self.assertIsNone(r.estimated_margin)

    def test_missing_seasonality_is_neutral_not_blocking(self):
        r = score_candidate(make_candidate(), signal(seasonality=None), TH, PC)
        self.assertTrue(r.passed, r.reasons)

    def test_custom_threshold_changes_outcome(self):
        strict = TrendThresholds(min_demand_growth=0.9)
        r = score_candidate(make_candidate(), signal(demand_growth=0.8), strict, PC)
        self.assertFalse(r.passed)

    def test_higher_growth_gives_higher_score(self):
        a = score_candidate(make_candidate(), signal(demand_growth=0.4), TH, PC)
        b = score_candidate(make_candidate(), signal(demand_growth=0.9), TH, PC)
        self.assertGreater(b.score, a.score)

    def test_rank_puts_passed_first_then_score(self):
        good = score_candidate(make_candidate(sku="A"), signal(sku="A"), TH, PC)
        bad = score_candidate(make_candidate(sku="B"), signal(sku="B", demand_growth=0.01), TH, PC)
        self.assertEqual([r.candidate.sku for r in rank([bad, good])], ["A", "B"])


class TestSources(unittest.TestCase):
    def test_mock_source_is_marked_mock(self):
        sup = MockSupplier()
        src = MockTrendSource()
        for c in sup.search_products("casa"):
            self.assertEqual(src.get_signal(c).source, "MOCK")
            self.assertEqual(c.source, "MOCK")

    def test_mock_source_unknown_sku_returns_missing_data(self):
        s = MockTrendSource().get_signal(make_candidate(sku="SCONOSCIUTO"))
        self.assertIsNone(s.demand_growth)
        self.assertIsNone(s.ad_saturation)

    def test_serpapi_source_computes_growth_from_timeseries(self):
        timeline = [{"values": [{"extracted_value": v}]} for v in [10] * 4 + [20] * 4]
        t = FakeTransport([(200, {"interest_over_time": {"timeline_data": timeline}})])
        src = SerpApiTrendSource(api_key="k-test", transport=t)
        s = src.get_signal(make_candidate())
        self.assertAlmostEqual(s.demand_growth, 1.0)
        self.assertIsNone(s.ad_saturation)  # nessun token Meta -> DATO MANCANTE
        self.assertEqual(s.source, "SERPAPI")
        self.assertTrue(t.calls[0]["url"].startswith("https://serpapi.com/"))

    def test_serpapi_uses_meta_ad_library_for_saturation(self):
        timeline = [{"values": [{"extracted_value": 10}]} for _ in range(8)]
        t = FakeTransport(
            [
                (200, {"interest_over_time": {"timeline_data": timeline}}),
                (200, {"data": [{}] * 50}),
            ]
        )
        src = SerpApiTrendSource(api_key="k", meta_token="m", transport=t, saturation_ads_ceiling=100)
        s = src.get_signal(make_candidate())
        self.assertAlmostEqual(s.ad_saturation, 0.5)
        self.assertIn("graph.facebook.com", t.calls[1]["url"])

    def test_serpapi_degrades_on_empty_data(self):
        t = FakeTransport([(200, {})])
        s = SerpApiTrendSource(api_key="k", transport=t).get_signal(make_candidate())
        self.assertIsNone(s.demand_growth)


class TestScanService(unittest.TestCase):
    def test_scan_mock_end_to_end_ranks_and_dedupes(self):
        results = scan(MockSupplier(), MockTrendSource(), ["casa", "casa"], TH, PC)
        skus = [r.candidate.sku for r in results]
        self.assertEqual(len(skus), len(set(skus)))
        self.assertTrue(any(r.passed for r in results))
        self.assertTrue(any(not r.passed for r in results))


if __name__ == "__main__":
    unittest.main()
