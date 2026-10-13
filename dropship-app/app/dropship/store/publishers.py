"""Pubblicazione store: interfaccia, MOCK e adapter reale Shopify Admin API (REST)."""

import hashlib
import re
from abc import ABC, abstractmethod

from dropship.http import request_json
from dropship.models import MOCK, Customer, Order, PublishResult
from dropship.secrets_util import Secret

_SHOP_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}\.myshopify\.com$")


class StorePublisher(ABC):
    source = "?"

    @abstractmethod
    def publish(self, payload):
        """Crea il prodotto. Restituisce PublishResult."""

    @abstractmethod
    def list_paid_unfulfilled_orders(self):
        """Ordini pagati e non evasi (lista di Order)."""


class MockStorePublisher(StorePublisher):
    """Store finto in memoria. Genera un ordine di esempio per ogni SKU indicato."""

    source = MOCK

    def __init__(self, order_skus=()):
        self.published = []
        self.order_skus = list(order_skus)

    def publish(self, payload):
        self.published.append(payload)
        pid = "MOCK-PROD-" + hashlib.sha256(payload["product"]["title"].encode()).hexdigest()[:8]
        return PublishResult(product_id=pid, status=payload["product"]["status"], source=MOCK)

    def list_paid_unfulfilled_orders(self):
        orders = []
        for i, sku in enumerate(self.order_skus, start=1):
            orders.append(
                Order(
                    order_id=f"MOCK-ORD-{i:04d}", sku=sku, quantity=1,
                    customer=Customer("Cliente Esempio", "Via di Prova 1", "Milano", "20100", "IT",
                                      "cliente@example.com"),
                    paid=True, source=MOCK,
                )
            )
        # un ordine NON pagato per mostrare il guardrail
        if self.order_skus:
            orders.append(
                Order(
                    order_id="MOCK-ORD-UNPAID", sku=self.order_skus[0], quantity=1,
                    customer=Customer("Cliente Esempio", "Via di Prova 2", "Roma", "00100", "IT"),
                    paid=False, source=MOCK,
                )
            )
        return orders


class ShopifyStorePublisher(StorePublisher):
    """Shopify Admin REST API. Il dominio è validato (*.myshopify.com) per evitare SSRF."""

    source = "SHOPIFY"

    def __init__(self, shop_domain, access_token, api_version="2025-07", transport=None):
        domain = str(shop_domain or "").strip().lower()
        if not _SHOP_RE.match(domain):
            raise ValueError("SHOPIFY_STORE_DOMAIN deve essere nel formato <negozio>.myshopify.com")
        if not re.match(r"^\d{4}-\d{2}$", str(api_version)):
            raise ValueError("SHOPIFY_API_VERSION non valida (formato AAAA-MM)")
        self.domain = domain
        self.api_version = api_version
        self._token = Secret(access_token)
        self._transport = transport

    def __repr__(self):
        return f"ShopifyStorePublisher(domain={self.domain!r}, token=***)"

    def _url(self, path):
        return f"https://{self.domain}/admin/api/{self.api_version}/{path}"

    def _headers(self):
        return {"X-Shopify-Access-Token": self._token.reveal()}

    def publish(self, payload):
        data = request_json("POST", self._url("products.json"), headers=self._headers(), payload=payload,
                            transport=self._transport, service="Shopify")
        prod = (data or {}).get("product") or {}
        if "id" not in prod:
            raise RuntimeError("Shopify: id prodotto mancante nella risposta")
        return PublishResult(product_id=str(prod["id"]), status=str(prod.get("status", "")), source=self.source)

    def list_paid_unfulfilled_orders(self):
        data = request_json(
            "GET", self._url("orders.json"), headers=self._headers(), transport=self._transport, service="Shopify",
            params={"status": "open", "financial_status": "paid", "fulfillment_status": "unfulfilled", "limit": 50},
        )
        out = []
        for o in (data or {}).get("orders", []):
            addr = o.get("shipping_address") or {}
            cust = Customer(
                name=str(addr.get("name", "")), address_line=str(addr.get("address1", "")),
                city=str(addr.get("city", "")), postal_code=str(addr.get("zip", "")),
                country=str(addr.get("country_code", "")), email=str(o.get("email", "")),
            )
            for li in o.get("line_items", []):
                out.append(
                    Order(
                        order_id=f"{o.get('id')}-{li.get('id')}", sku=str(li.get("sku", "")),
                        quantity=int(li.get("quantity", 0)), customer=cust,
                        paid=o.get("financial_status") == "paid", source=self.source,
                    )
                )
        return out
