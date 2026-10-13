import unittest

from dropship import adapters
from dropship.campaigns.platforms import GoogleAds, MetaAds, MockAds, TikTokAds
from dropship.orders.suppliers import CJDropshippingSupplier, MockSupplier
from dropship.store.copywriter import MockCopywriter
from dropship.store.publishers import MockStorePublisher, ShopifyStorePublisher
from dropship.trends.sources import MockTrendSource, SerpApiTrendSource


class TestFactoryDegradesGracefully(unittest.TestCase):
    def test_no_keys_means_all_mock(self):
        env = {}
        self.assertIsInstance(adapters.build_supplier(env), MockSupplier)
        self.assertIsInstance(adapters.build_trend_source(env), MockTrendSource)
        self.assertIsInstance(adapters.build_store(env), MockStorePublisher)
        self.assertIsInstance(adapters.build_copywriter(env), MockCopywriter)
        ads = adapters.build_ads(env)
        self.assertEqual(set(ads), {"meta", "tiktok", "google"})
        self.assertTrue(all(isinstance(a, MockAds) for a in ads.values()))
        self.assertTrue(all(a.source == "MOCK" for a in ads.values()))

    def test_keys_select_real_adapters(self):
        env = {
            "CJ_API_KEY": "x",
            "SERPAPI_API_KEY": "x",
            "SHOPIFY_STORE_DOMAIN": "negozio.myshopify.com",
            "SHOPIFY_ADMIN_TOKEN": "x",
            "META_ADS_ACCESS_TOKEN": "x",
            "META_AD_ACCOUNT_ID": "1",
            "TIKTOK_ACCESS_TOKEN": "x",
            "TIKTOK_ADVERTISER_ID": "2",
            "GOOGLE_ADS_DEVELOPER_TOKEN": "x",
            "GOOGLE_ADS_CLIENT_ID": "x",
            "GOOGLE_ADS_CLIENT_SECRET": "x",
            "GOOGLE_ADS_REFRESH_TOKEN": "x",
            "GOOGLE_ADS_CUSTOMER_ID": "3",
        }
        self.assertIsInstance(adapters.build_supplier(env), CJDropshippingSupplier)
        self.assertIsInstance(adapters.build_trend_source(env), SerpApiTrendSource)
        self.assertIsInstance(adapters.build_store(env), ShopifyStorePublisher)
        ads = adapters.build_ads(env)
        self.assertIsInstance(ads["meta"], MetaAds)
        self.assertIsInstance(ads["tiktok"], TikTokAds)
        self.assertIsInstance(ads["google"], GoogleAds)

    def test_partial_keys_fall_back_to_mock(self):
        env = {"META_ADS_ACCESS_TOKEN": "x", "SHOPIFY_ADMIN_TOKEN": "x"}
        self.assertIsInstance(adapters.build_ads(env)["meta"], MockAds)
        self.assertIsInstance(adapters.build_store(env), MockStorePublisher)

    def test_force_mock_overrides_keys(self):
        env = {"CJ_API_KEY": "x", "DROPSHIP_FORCE_MOCK": "1"}
        self.assertIsInstance(adapters.build_supplier(env), MockSupplier)

    def test_anthropic_key_without_sdk_degrades_to_mock(self):
        env = {"ANTHROPIC_API_KEY": "x"}
        cw = adapters.build_copywriter(env, sdk_available=False)
        self.assertIsInstance(cw, MockCopywriter)

    def test_describe_reports_mode_without_secrets(self):
        env = {"CJ_API_KEY": "SEGRETO"}
        lines = adapters.describe_modes(env)
        text = "\n".join(lines)
        self.assertIn("CJ", text)
        self.assertIn("MOCK", text)
        self.assertNotIn("SEGRETO", text)


if __name__ == "__main__":
    unittest.main()
