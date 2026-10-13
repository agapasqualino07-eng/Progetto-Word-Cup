"""Piattaforme ads: interfaccia, MOCK e adapter reali (Meta, TikTok, Google Ads).

Regola comune: le campagne vengono SEMPRE create in pausa. L'attivazione passa
dall'approvazione umana (CampaignManager.activate).
Gli endpoint reali vanno verificati sulla documentazione ufficiale e sulla
versione API corrente prima dell'uso in produzione.
"""

import hashlib
import json
import re
from abc import ABC, abstractmethod
from decimal import Decimal

from dropship.http import request_json
from dropship.models import MOCK, AdMetrics
from dropship.secrets_util import Secret


class AdsPlatform(ABC):
    source = "?"
    platform = "?"

    @abstractmethod
    def create_paused_campaign(self, campaign, product_title):
        """Crea la campagna in pausa. Restituisce l'id esterno."""

    @abstractmethod
    def set_daily_budget(self, external_id, amount):
        pass

    @abstractmethod
    def set_status(self, external_id, active):
        pass

    @abstractmethod
    def get_metrics(self, external_id):
        """AdMetrics(spend, revenue) del giorno."""


class MockAds(AdsPlatform):
    source = MOCK

    def __init__(self, platform):
        self.platform = platform
        self.campaigns = {}
        self._metrics = {}

    def create_paused_campaign(self, campaign, product_title):
        ext = f"MOCK-{self.platform.upper()}-" + hashlib.sha256(campaign.campaign_id.encode()).hexdigest()[:8]
        self.campaigns[ext] = {"status": "PAUSED", "daily_budget": str(campaign.daily_budget), "name": product_title}
        return ext

    # il mock non persiste tra processi CLI: un id sconosciuto viene ricreato in memoria
    def set_daily_budget(self, external_id, amount):
        self.campaigns.setdefault(external_id, {"status": "PAUSED"})["daily_budget"] = str(amount)

    def set_status(self, external_id, active):
        self.campaigns.setdefault(external_id, {})["status"] = "ACTIVE" if active else "PAUSED"

    def set_metrics(self, external_id, spend, revenue):
        self._metrics[external_id] = (Decimal(spend), Decimal(revenue))

    def get_metrics(self, external_id):
        if external_id in self._metrics:
            spend, revenue = self._metrics[external_id]
        else:
            # metriche dimostrative deterministiche (NON reali)
            h = int(hashlib.sha256(external_id.encode()).hexdigest()[:4], 16)
            spend = Decimal(10 + h % 15)
            revenue = (spend * Decimal(h % 40) / Decimal(10)).quantize(Decimal("0.01"))
        return AdMetrics(spend=spend, revenue=revenue, source=MOCK)


def _cents(amount):
    return int((Decimal(amount) * 100).to_integral_value())


class MetaAds(AdsPlatform):
    """Meta Marketing API (Graph). Campagna CBO con daily_budget in centesimi, status PAUSED."""

    source = "META"
    platform = "meta"

    def __init__(self, access_token, ad_account_id, api_version="v21.0", transport=None):
        if not re.match(r"^\d{1,20}$", str(ad_account_id).removeprefix("act_")):
            raise ValueError("META_AD_ACCOUNT_ID deve essere numerico")
        if not re.match(r"^v\d+\.\d+$", api_version):
            raise ValueError("versione Graph API non valida")
        self.account = str(ad_account_id).removeprefix("act_")
        self.base = f"https://graph.facebook.com/{api_version}"
        self._token = Secret(access_token)
        self._transport = transport

    def __repr__(self):
        return f"MetaAds(account={self.account!r}, token=***)"

    def _req(self, method, path, **kw):
        return request_json(method, f"{self.base}/{path}", transport=self._transport, service="Meta Ads",
                            headers={"Authorization": f"Bearer {self._token.reveal()}"}, **kw)

    def create_paused_campaign(self, campaign, product_title):
        data = self._req("POST", f"act_{self.account}/campaigns", payload={
            "name": f"[DRAFT] {product_title}"[:200],
            "objective": "OUTCOME_SALES",
            "status": "PAUSED",
            "special_ad_categories": [],
            "daily_budget": _cents(campaign.daily_budget),
        })
        if not data.get("id"):
            raise RuntimeError("Meta Ads: id campagna mancante")
        return str(data["id"])

    def set_daily_budget(self, external_id, amount):
        self._req("POST", str(external_id), payload={"daily_budget": _cents(amount)})

    def set_status(self, external_id, active):
        self._req("POST", str(external_id), payload={"status": "ACTIVE" if active else "PAUSED"})

    def get_metrics(self, external_id):
        data = self._req("GET", f"{external_id}/insights",
                         params={"fields": "spend,action_values", "date_preset": "today"})
        row = (data.get("data") or [{}])[0]
        revenue = sum(
            Decimal(str(a.get("value", "0"))) for a in row.get("action_values", [])
            if a.get("action_type") in ("purchase", "omni_purchase")
        )
        return AdMetrics(spend=Decimal(str(row.get("spend", "0"))), revenue=Decimal(revenue), source=self.source)


class TikTokAds(AdsPlatform):
    """TikTok Business API v1.3. operation_status DISABLE = in pausa."""

    source = "TIKTOK"
    platform = "tiktok"
    BASE = "https://business-api.tiktok.com/open_api/v1.3"

    def __init__(self, access_token, advertiser_id, transport=None):
        if not re.match(r"^\d{1,25}$", str(advertiser_id)):
            raise ValueError("TIKTOK_ADVERTISER_ID deve essere numerico")
        self.advertiser_id = str(advertiser_id)
        self._token = Secret(access_token)
        self._transport = transport

    def __repr__(self):
        return f"TikTokAds(advertiser={self.advertiser_id!r}, token=***)"

    def _req(self, method, path, **kw):
        data = request_json(method, f"{self.BASE}/{path}", transport=self._transport, service="TikTok Ads",
                            headers={"Access-Token": self._token.reveal()}, **kw)
        if data.get("code") != 0:
            raise RuntimeError(f"TikTok Ads: errore API (code {data.get('code')})")
        return data.get("data") or {}

    def create_paused_campaign(self, campaign, product_title):
        data = self._req("POST", "campaign/create/", payload={
            "advertiser_id": self.advertiser_id,
            "campaign_name": f"[DRAFT] {product_title}"[:100],
            "objective_type": "WEB_CONVERSIONS",
            "budget_mode": "BUDGET_MODE_DAY",
            "budget": float(campaign.daily_budget),
            "operation_status": "DISABLE",
        })
        if not data.get("campaign_id"):
            raise RuntimeError("TikTok Ads: campaign_id mancante")
        return str(data["campaign_id"])

    def set_daily_budget(self, external_id, amount):
        self._req("POST", "campaign/update/", payload={
            "advertiser_id": self.advertiser_id, "campaign_id": str(external_id), "budget": float(amount)})

    def set_status(self, external_id, active):
        self._req("POST", "campaign/status/update/", payload={
            "advertiser_id": self.advertiser_id, "campaign_ids": [str(external_id)],
            "operation_status": "ENABLE" if active else "DISABLE"})

    def get_metrics(self, external_id):
        data = self._req("GET", "report/integrated/get/", params={
            "advertiser_id": self.advertiser_id, "report_type": "BASIC", "data_level": "AUCTION_CAMPAIGN",
            "dimensions": json.dumps(["campaign_id"]),
            "metrics": json.dumps(["spend", "complete_payment_roas"]),
            "filtering": json.dumps([{"field_name": "campaign_ids", "filter_type": "IN",
                                      "filter_value": json.dumps([str(external_id)])}]),
        })
        rows = data.get("list") or [{}]
        m = rows[0].get("metrics", {})
        spend = Decimal(str(m.get("spend") or "0"))
        # se il ROAS acquisti manca, ricavi = 0 => lo stop-loss agisce in modo prudente
        roas = Decimal(str(m.get("complete_payment_roas") or "0"))
        return AdMetrics(spend=spend, revenue=(spend * roas).quantize(Decimal("0.01")), source=self.source)


class GoogleAds(AdsPlatform):
    """Google Ads API (REST). OAuth2 refresh token -> access token; budget + campagna PAUSED."""

    source = "GOOGLE_ADS"
    platform = "google"
    TOKEN_URL = "https://oauth2.googleapis.com/token"

    def __init__(self, developer_token, client_id, client_secret, refresh_token, customer_id,
                 login_customer_id=None, api_version="v21", transport=None):
        cid = str(customer_id).replace("-", "")
        if not re.match(r"^\d{1,12}$", cid):
            raise ValueError("GOOGLE_ADS_CUSTOMER_ID deve essere numerico")
        if not re.match(r"^v\d+$", api_version):
            raise ValueError("versione Google Ads API non valida")
        self.customer_id = cid
        self.login_customer_id = str(login_customer_id).replace("-", "") if login_customer_id else None
        self.base = f"https://googleads.googleapis.com/{api_version}/customers/{cid}"
        self._dev = Secret(developer_token)
        self._client_id = client_id
        self._client_secret = Secret(client_secret)
        self._refresh = Secret(refresh_token)
        self._transport = transport
        self._access = None

    def __repr__(self):
        return f"GoogleAds(customer={self.customer_id!r}, tokens=***)"

    def _headers(self):
        if self._access is None:
            data = request_json("POST", self.TOKEN_URL, transport=self._transport, service="Google OAuth", form={
                "grant_type": "refresh_token", "client_id": self._client_id,
                "client_secret": self._client_secret.reveal(), "refresh_token": self._refresh.reveal()})
            if not data.get("access_token"):
                raise RuntimeError("Google OAuth: access token mancante")
            self._access = Secret(data["access_token"])
        h = {"Authorization": f"Bearer {self._access.reveal()}", "developer-token": self._dev.reveal()}
        if self.login_customer_id:
            h["login-customer-id"] = self.login_customer_id
        return h

    def _mutate(self, resource, operations):
        data = request_json("POST", f"{self.base}/{resource}:mutate", headers=self._headers(),
                            payload={"operations": operations}, transport=self._transport, service="Google Ads")
        results = data.get("results") or []
        if not results or not results[0].get("resourceName"):
            raise RuntimeError("Google Ads: mutate senza risultati")
        return results[0]["resourceName"]

    def create_paused_campaign(self, campaign, product_title):
        budget_rn = self._mutate("campaignBudgets", [{"create": {
            "name": f"budget {campaign.campaign_id}",
            "amountMicros": str(int(Decimal(campaign.daily_budget) * 1_000_000)),
            "deliveryMethod": "STANDARD",
            "explicitlyShared": False,
        }}])
        return self._mutate("campaigns", [{"create": {
            "name": f"[DRAFT] {product_title}"[:200],
            "status": "PAUSED",
            "advertisingChannelType": "SEARCH",
            "campaignBudget": budget_rn,
            "maximizeConversionValue": {},
            "containsEuPoliticalAdvertising": "DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING",
            "networkSettings": {"targetGoogleSearch": True, "targetSearchNetwork": False},
        }}])

    def set_daily_budget(self, external_id, amount):
        data = request_json("POST", f"{self.base}/googleAds:search", headers=self._headers(),
                            payload={"query": "SELECT campaign.campaign_budget FROM campaign "
                                              f"WHERE campaign.resource_name = '{_gaql_rn(external_id)}'"},
                            transport=self._transport, service="Google Ads")
        rows = data.get("results") or []
        if not rows:
            raise RuntimeError("Google Ads: campagna non trovata")
        budget_rn = rows[0]["campaign"]["campaignBudget"]
        self._mutate("campaignBudgets", [{"update": {"resourceName": budget_rn,
                                                     "amountMicros": str(int(Decimal(amount) * 1_000_000))},
                                          "updateMask": "amountMicros"}])

    def set_status(self, external_id, active):
        self._mutate("campaigns", [{"update": {"resourceName": str(external_id),
                                               "status": "ENABLED" if active else "PAUSED"},
                                    "updateMask": "status"}])

    def get_metrics(self, external_id):
        data = request_json("POST", f"{self.base}/googleAds:search", headers=self._headers(),
                            payload={"query": "SELECT metrics.cost_micros, metrics.conversions_value FROM campaign "
                                              f"WHERE campaign.resource_name = '{_gaql_rn(external_id)}' "
                                              "AND segments.date DURING TODAY"},
                            transport=self._transport, service="Google Ads")
        rows = data.get("results") or [{}]
        m = rows[0].get("metrics", {})
        spend = Decimal(str(m.get("costMicros", "0"))) / 1_000_000
        return AdMetrics(spend=spend, revenue=Decimal(str(m.get("conversionsValue", "0"))), source=self.source)


def _gaql_rn(resource_name):
    rn = str(resource_name)
    if not re.match(r"^customers/\d+/campaigns/\d+$", rn):
        raise ValueError("resource name Google Ads non valido")  # anti-injection GAQL
    return rn
