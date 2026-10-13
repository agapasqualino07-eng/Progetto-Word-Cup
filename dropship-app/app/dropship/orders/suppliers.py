"""Fornitori: interfaccia, adapter MOCK e adapter reale CJdropshipping.

Il catalogo MOCK contiene volutamente prodotti vietati/regolati per mostrare
i guardrail in azione. Tutti i dati mock hanno source="MOCK".
"""

import hashlib
from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation

from dropship.http import ExternalServiceError, request_json
from dropship.models import MOCK, ProductCandidate, SupplierOrder, Tracking
from dropship.secrets_util import Secret


class Supplier(ABC):
    source = "?"

    @abstractmethod
    def search_products(self, keyword):
        """Restituisce una lista di ProductCandidate."""

    @abstractmethod
    def place_order(self, order):
        """Inoltra l'ordine al fornitore. Restituisce SupplierOrder."""

    @abstractmethod
    def get_tracking(self, supplier_order_id):
        """Restituisce Tracking."""


def _c(sku, title, category, cost, ship, weight, keyword, market, desc, certs=(), brand=None):
    return ProductCandidate(
        sku=sku, title=title, category=category, supplier_cost=Decimal(cost),
        shipping_cost=Decimal(ship), weight_kg=weight, keyword=keyword, source=MOCK,
        market_price=Decimal(market) if market else None, description=desc,
        certifications=tuple(certs), brand=brand,
    )


MOCK_CATALOG = (
    _c("MOCK-LAMP-01", "Lampada LED pieghevole da scrivania", "electronics", "7.80", "3.20", 0.6,
       "casa", "34.90", "Luce regolabile in 3 tonalità, ricarica USB-C.", ("CE", "RoHS")),
    _c("MOCK-ORG-02", "Organizer da cassetto in bambù", "home", "6.50", "2.90", 0.8,
       "casa", "29.90", "Set modulare di 6 scomparti in bambù naturale."),
    _c("MOCK-PET-03", "Spazzola autopulente per animali", "pets", "3.10", "2.10", 0.2,
       "animali", "19.90", "Rimuove il pelo morto, pulsante di rilascio rapido."),
    _c("MOCK-SERUM-04", "Siero viso alla vitamina C", "cosmetics", "2.40", "2.00", 0.1,
       "beauty", "24.90", "Siero illuminante 30 ml."),
    _c("MOCK-COLL-05", "Integratore di collagene in polvere", "health", "4.00", "2.50", 0.3,
       "beauty", "29.90", "Polvere solubile al gusto frutti rossi."),
    _c("MOCK-WATCH-06", "Orologio replica stile Rolex", "fashion", "12.00", "3.50", 0.2,
       "moda", "89.90", "Quadrante acciaio, cinturino in metallo."),
    _c("MOCK-CHRG-07", "Caricatore wireless 15W", "electronics", "4.20", "2.30", 0.15,
       "tech", "22.90", "Ricarica rapida Qi per smartphone."),
    _c("MOCK-BOTL-08", "Borraccia termica con display temperatura", "home", "5.40", "2.60", 0.4,
       "casa", "24.90", "Acciaio inox doppia parete, 500 ml."),
    _c("MOCK-DESK-09", "Scrivania pieghevole da parete", "home", "28.00", "18.00", 9.0,
       "casa", "119.90", "Tavolo a ribalta salvaspazio in legno."),
)


class MockSupplier(Supplier):
    """Fornitore finto: catalogo statico, ordini in memoria. Nessuna rete."""

    source = MOCK

    def __init__(self, catalog=MOCK_CATALOG):
        self.catalog = tuple(catalog)
        self.orders = {}

    def search_products(self, keyword):
        # demo: restituisce l'intero catalogo per qualunque keyword
        return list(self.catalog)

    def place_order(self, order):
        sid = "MOCK-SUP-" + hashlib.sha256(order.order_id.encode()).hexdigest()[:8]
        self.orders[sid] = {"order_id": order.order_id, "sku": order.sku, "quantity": order.quantity}
        return SupplierOrder(supplier_order_id=sid, status="CREATED", source=MOCK)

    def get_tracking(self, supplier_order_id):
        digest = hashlib.sha256(supplier_order_id.encode()).hexdigest()[:10].upper()
        return Tracking(
            tracking_number=f"MOCKTRK{digest}", carrier="MOCK-POST", status="IN_TRANSITO", source=MOCK
        )


class CJDropshippingSupplier(Supplier):
    """Adapter reale CJdropshipping (API v2). Verificare endpoint/campi sulla doc ufficiale
    (https://developers.cjdropshipping.com) prima dell'uso in produzione.

    Prezzi CJ in USD: la conversione usa ``usd_to_eur`` (CJ_USD_EUR_RATE). Se manca,
    la ricerca prodotti fallisce in modo esplicito invece di inventare un cambio.
    """

    source = "CJ"
    BASE = "https://developers.cjdropshipping.com/api2.0/v1"

    def __init__(self, api_key, transport=None, usd_to_eur=None, destination_country="IT", logistic_name=""):
        self._api_key = Secret(api_key)
        self._transport = transport
        self._token = None
        self.usd_to_eur = Decimal(str(usd_to_eur)) if usd_to_eur else None
        self.destination_country = destination_country
        self.logistic_name = logistic_name

    def __repr__(self):
        return f"CJDropshippingSupplier(api_key=***, destination={self.destination_country!r})"

    def _call(self, method, path, **kw):
        data = request_json(method, self.BASE + path, transport=self._transport, service="CJdropshipping", **kw)
        if not isinstance(data, dict) or data.get("result") is False or (
            "code" in data and data.get("code") not in (200, "200")
        ):
            raise RuntimeError(f"CJdropshipping: richiesta rifiutata ({str(data.get('message', ''))[:80]})")
        return data.get("data")

    def _auth_headers(self):
        if self._token is None:
            data = self._call("POST", "/authentication/getAccessToken", payload={"apiKey": self._api_key.reveal()})
            token = (data or {}).get("accessToken")
            if not token:
                raise RuntimeError("CJdropshipping: token non ricevuto")
            self._token = Secret(token)
        return {"CJ-Access-Token": self._token.reveal()}

    def search_products(self, keyword):
        if self.usd_to_eur is None:
            raise ExternalServiceError("CJ_USD_EUR_RATE mancante: impossibile convertire i prezzi USD")
        data = self._call(
            "GET", "/product/list", headers=self._auth_headers(),
            params={"productNameEn": keyword, "pageNum": 1, "pageSize": 20},
        ) or {}
        out = []
        for item in data.get("list", [])[:20]:
            try:
                cost_usd = Decimal(str(item.get("sellPrice", "")).split("-")[0].strip())
                weight_g = float(str(item.get("productWeight", "0")).split("-")[-1] or 0)
            except (InvalidOperation, ValueError):
                continue
            sku = str(item.get("pid") or "")
            if not sku:
                continue
            shipping = self._freight_eur(sku)
            if shipping is None:
                continue  # niente costo spedizione = niente candidato (mai stime inventate)
            out.append(
                ProductCandidate(
                    sku=sku, title=str(item.get("productNameEn", ""))[:200],
                    category=str(item.get("categoryName", "")).lower()[:60],
                    supplier_cost=(cost_usd * self.usd_to_eur).quantize(Decimal("0.01")),
                    shipping_cost=shipping, weight_kg=weight_g / 1000.0, keyword=keyword,
                    source=self.source, market_price=None,
                    image_url=str(item.get("productImage", ""))[:500],
                )
            )
        return out

    def _freight_eur(self, pid):
        try:
            data = self._call(
                "POST", "/logistic/freightCalculate", headers=self._auth_headers(),
                payload={"startCountryCode": "CN", "endCountryCode": self.destination_country,
                         "products": [{"quantity": 1, "vid": pid}]},
            )
            prices = [Decimal(str(x["logisticPrice"])) for x in (data or []) if "logisticPrice" in x]
        except (RuntimeError, ExternalServiceError, InvalidOperation, KeyError, TypeError):
            return None
        if not prices:
            return None
        return (min(prices) * self.usd_to_eur).quantize(Decimal("0.01"))

    def place_order(self, order):
        c = order.customer
        payload = {
            "orderNumber": order.order_id,
            "shippingCountryCode": c.country,
            "shippingCity": c.city,
            "shippingZip": c.postal_code,
            "shippingAddress": c.address_line,
            "shippingCustomerName": c.name,
            "email": c.email,
            "fromCountryCode": "CN",
            "logisticName": self.logistic_name,
            "products": [{"vid": order.sku, "quantity": order.quantity}],
        }
        data = self._call("POST", "/shopping/order/createOrderV2", headers=self._auth_headers(), payload=payload) or {}
        oid = data.get("orderId")
        if not oid:
            raise RuntimeError("CJdropshipping: orderId mancante nella risposta")
        return SupplierOrder(supplier_order_id=str(oid), status=str(data.get("orderStatus", "CREATED")), source=self.source)

    def get_tracking(self, supplier_order_id):
        data = self._call(
            "GET", "/shopping/order/getOrderDetail", headers=self._auth_headers(),
            params={"orderId": supplier_order_id},
        ) or {}
        return Tracking(
            tracking_number=data.get("trackNumber") or None,
            carrier=str(data.get("logisticName") or "DATO MANCANTE"),
            status=str(data.get("orderStatus") or "DATO MANCANTE"),
            source=self.source,
        )
