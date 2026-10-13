"""Fonti di segnali di tendenza: interfaccia, MOCK e adapter reale SerpApi (+ Meta Ad Library).

Un segnale non disponibile resta ``None`` (= DATO MANCANTE): lo scoring lo
tratta come mancante, non lo stima.
"""

from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation
from statistics import median

from dropship.http import ExternalServiceError, request_json
from dropship.models import MOCK, TrendSignal
from dropship.secrets_util import Secret


class TrendSource(ABC):
    source = "?"

    @abstractmethod
    def get_signal(self, candidate):
        """Restituisce TrendSignal per il candidato."""

    def market_price(self, candidate):
        """Prezzo di mercato osservato (lordo) o None. Default: nessuna fonte."""
        return None


# (crescita domanda, saturazione ads, stagionalità) — valori dimostrativi, NON reali.
MOCK_SIGNALS = {
    "MOCK-LAMP-01": (0.65, 0.35, 0.80),
    "MOCK-ORG-02": (0.48, 0.25, 0.60),
    "MOCK-PET-03": (0.90, 0.45, 0.70),
    "MOCK-SERUM-04": (1.20, 0.55, 0.60),
    "MOCK-COLL-05": (1.50, 0.70, 0.50),
    "MOCK-WATCH-06": (0.40, 0.30, 0.50),
    "MOCK-CHRG-07": (0.55, 0.40, 0.50),
    "MOCK-BOTL-08": (0.70, 0.85, 0.40),
    "MOCK-DESK-09": (0.35, 0.20, 0.50),
}


class MockTrendSource(TrendSource):
    source = MOCK

    def __init__(self, signals=None):
        self.signals = dict(MOCK_SIGNALS if signals is None else signals)

    def get_signal(self, candidate):
        g, s, season = self.signals.get(candidate.sku, (None, None, None))
        return TrendSignal(candidate.sku, g, s, season, MOCK)


class SerpApiTrendSource(TrendSource):
    """Crescita domanda da Google Trends (via SerpApi), saturazione da Meta Ad Library
    (opzionale, token separato), prezzo di mercato da Google Shopping (via SerpApi).

    - crescita = media ultime 4 settimane / media 4 settimane precedenti - 1
    - saturazione = min(1, n. inserzioni attive / saturation_ads_ceiling)
    """

    source = "SERPAPI"
    SERP_URL = "https://serpapi.com/search.json"
    META_URL = "https://graph.facebook.com/v21.0/ads_archive"

    def __init__(self, api_key, meta_token=None, transport=None, geo="IT", saturation_ads_ceiling=200,
                 meta_api_version=None):
        self._api_key = Secret(api_key)
        self._meta_token = Secret(meta_token) if meta_token else None
        self._transport = transport
        self.geo = geo
        self.saturation_ads_ceiling = max(1, int(saturation_ads_ceiling))
        if meta_api_version:
            self.META_URL = f"https://graph.facebook.com/{meta_api_version}/ads_archive"

    def __repr__(self):
        return f"SerpApiTrendSource(api_key=***, meta={'***' if self._meta_token else None}, geo={self.geo!r})"

    def _growth(self, keyword):
        data = request_json(
            "GET", self.SERP_URL, transport=self._transport, service="SerpApi",
            params={"engine": "google_trends", "q": keyword, "geo": self.geo,
                    "date": "today 3-m", "data_type": "TIMESERIES", "api_key": self._api_key.reveal()},
        )
        timeline = ((data or {}).get("interest_over_time") or {}).get("timeline_data") or []
        values = []
        for point in timeline:
            try:
                values.append(float(point["values"][0]["extracted_value"]))
            except (KeyError, IndexError, TypeError, ValueError):
                continue
        if len(values) < 8:
            return None
        recent, previous = values[-4:], values[-8:-4]
        prev_avg = sum(previous) / 4
        if prev_avg <= 0:
            return None
        return sum(recent) / 4 / prev_avg - 1

    def _saturation(self, keyword):
        if self._meta_token is None:
            return None
        data = request_json(
            "GET", self.META_URL, transport=self._transport, service="Meta Ad Library",
            headers={"Authorization": f"Bearer {self._meta_token.reveal()}"},
            params={"search_terms": keyword, "ad_reached_countries": f'["{self.geo}"]',
                    "ad_active_status": "ACTIVE", "fields": "id", "limit": 500},
        )
        ads = (data or {}).get("data")
        if not isinstance(ads, list):
            return None
        return min(1.0, len(ads) / self.saturation_ads_ceiling)

    def get_signal(self, candidate):
        kw = candidate.keyword or candidate.title
        try:
            growth = self._growth(kw)
        except ExternalServiceError:
            growth = None
        try:
            saturation = self._saturation(kw)
        except ExternalServiceError:
            saturation = None
        return TrendSignal(candidate.sku, growth, saturation, None, self.source)

    def market_price(self, candidate):
        try:
            data = request_json(
                "GET", self.SERP_URL, transport=self._transport, service="SerpApi",
                params={"engine": "google_shopping", "q": candidate.title, "gl": self.geo.lower(),
                        "hl": "it", "api_key": self._api_key.reveal()},
            )
        except ExternalServiceError:
            return None
        prices = []
        for r in (data or {}).get("shopping_results", [])[:40]:
            try:
                prices.append(Decimal(str(r["extracted_price"])))
            except (KeyError, InvalidOperation, TypeError):
                continue
        if len(prices) < 3:  # campione troppo piccolo: DATO MANCANTE
            return None
        return Decimal(median(prices)).quantize(Decimal("0.01"))
