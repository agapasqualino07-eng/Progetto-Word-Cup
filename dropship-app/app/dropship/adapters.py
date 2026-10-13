"""Factory degli adapter: reale se TUTTE le chiavi richieste sono presenti, altrimenti MOCK.

``DROPSHIP_FORCE_MOCK=1`` forza il mock anche in presenza di chiavi.
Le funzioni ricevono l'ambiente come dizionario (testabili senza toccare os.environ).
"""

import importlib.util

from dropship.campaigns.platforms import GoogleAds, MetaAds, MockAds, TikTokAds
from dropship.config import is_truthy
from dropship.orders.suppliers import CJDropshippingSupplier, MockSupplier
from dropship.store.copywriter import DEFAULT_MODEL, AnthropicCopywriter, MockCopywriter
from dropship.store.publishers import MockStorePublisher, ShopifyStorePublisher
from dropship.trends.sources import MockTrendSource, SerpApiTrendSource

REQUIRED = {
    "supplier (CJdropshipping)": ("CJ_API_KEY",),
    "trend (SerpApi)": ("SERPAPI_API_KEY",),
    "store (Shopify)": ("SHOPIFY_STORE_DOMAIN", "SHOPIFY_ADMIN_TOKEN"),
    "ads meta": ("META_ADS_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"),
    "ads tiktok": ("TIKTOK_ACCESS_TOKEN", "TIKTOK_ADVERTISER_ID"),
    "ads google": (
        "GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CLIENT_ID", "GOOGLE_ADS_CLIENT_SECRET",
        "GOOGLE_ADS_REFRESH_TOKEN", "GOOGLE_ADS_CUSTOMER_ID",
    ),
    "copy (Anthropic)": ("ANTHROPIC_API_KEY",),
}


def _has(env, *names):
    if is_truthy(env.get("DROPSHIP_FORCE_MOCK")):
        return False
    return all(str(env.get(n) or "").strip() for n in names)


def build_supplier(env):
    if _has(env, *REQUIRED["supplier (CJdropshipping)"]):
        return CJDropshippingSupplier(
            api_key=env["CJ_API_KEY"],
            usd_to_eur=env.get("CJ_USD_EUR_RATE") or None,
            destination_country=env.get("DROPSHIP_DEST_COUNTRY", "IT"),
            logistic_name=env.get("CJ_LOGISTIC_NAME", ""),
        )
    return MockSupplier()


def build_trend_source(env):
    if _has(env, *REQUIRED["trend (SerpApi)"]):
        return SerpApiTrendSource(
            api_key=env["SERPAPI_API_KEY"],
            meta_token=env.get("META_AD_LIBRARY_TOKEN") or None,
            geo=env.get("DROPSHIP_DEST_COUNTRY", "IT"),
        )
    return MockTrendSource()


def build_store(env, mock_order_skus=()):
    if _has(env, *REQUIRED["store (Shopify)"]):
        return ShopifyStorePublisher(
            shop_domain=env["SHOPIFY_STORE_DOMAIN"],
            access_token=env["SHOPIFY_ADMIN_TOKEN"],
            api_version=env.get("SHOPIFY_API_VERSION") or "2025-07",
        )
    return MockStorePublisher(order_skus=mock_order_skus)


def build_copywriter(env, sdk_available=None):
    if sdk_available is None:
        sdk_available = importlib.util.find_spec("anthropic") is not None
    if _has(env, *REQUIRED["copy (Anthropic)"]) and sdk_available:
        return AnthropicCopywriter(api_key=env["ANTHROPIC_API_KEY"], model=env.get("ANTHROPIC_MODEL") or DEFAULT_MODEL)
    return MockCopywriter()


def build_ads(env):
    ads = {}
    if _has(env, *REQUIRED["ads meta"]):
        ads["meta"] = MetaAds(env["META_ADS_ACCESS_TOKEN"], env["META_AD_ACCOUNT_ID"],
                              api_version=env.get("META_API_VERSION") or "v21.0")
    else:
        ads["meta"] = MockAds("meta")
    if _has(env, *REQUIRED["ads tiktok"]):
        ads["tiktok"] = TikTokAds(env["TIKTOK_ACCESS_TOKEN"], env["TIKTOK_ADVERTISER_ID"])
    else:
        ads["tiktok"] = MockAds("tiktok")
    if _has(env, *REQUIRED["ads google"]):
        ads["google"] = GoogleAds(
            developer_token=env["GOOGLE_ADS_DEVELOPER_TOKEN"], client_id=env["GOOGLE_ADS_CLIENT_ID"],
            client_secret=env["GOOGLE_ADS_CLIENT_SECRET"], refresh_token=env["GOOGLE_ADS_REFRESH_TOKEN"],
            customer_id=env["GOOGLE_ADS_CUSTOMER_ID"],
            login_customer_id=env.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID") or None,
            api_version=env.get("GOOGLE_ADS_API_VERSION") or "v21",
        )
    else:
        ads["google"] = MockAds("google")
    return ads


def describe_modes(env):
    """Righe leggibili 'connettore: REALE/MOCK' (mai valori delle chiavi)."""
    lines = []
    for name, keys in REQUIRED.items():
        if _has(env, *keys):
            lines.append(f"{name}: REALE")
        else:
            missing = [k for k in keys if not str(env.get(k) or "").strip()]
            why = "forzato da DROPSHIP_FORCE_MOCK" if is_truthy(env.get("DROPSHIP_FORCE_MOCK")) else (
                "mancano " + ", ".join(missing))
            lines.append(f"{name}: MOCK ({why})")
    return lines
