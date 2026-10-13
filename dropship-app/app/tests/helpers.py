"""Helper condivisi dai test: fabbriche di oggetti e un transport HTTP finto.

Nessun test deve fare chiamate di rete: gli adapter reali ricevono
``FakeTransport`` che registra le richieste e restituisce risposte preconfezionate.
"""

import json
from decimal import Decimal

from dropship.models import Customer, Order, ProductCandidate


def make_candidate(**overrides):
    data = dict(
        sku="SKU-1",
        title="Lampada LED da scrivania",
        category="home",
        supplier_cost=Decimal("8.00"),
        shipping_cost=Decimal("3.00"),
        weight_kg=0.5,
        keyword="lampada led",
        source="MOCK",
        market_price=Decimal("39.90"),
        description="Lampada pieghevole con luce regolabile.",
        certifications=("CE",),
    )
    data.update(overrides)
    return ProductCandidate(**data)


def make_customer(**overrides):
    data = dict(
        name="Mario Rossi",
        address_line="Via Roma 1",
        city="Milano",
        postal_code="20100",
        country="IT",
        email="mario@example.com",
    )
    data.update(overrides)
    return Customer(**data)


def make_order(**overrides):
    data = dict(
        order_id="ORD-1",
        sku="SKU-1",
        quantity=1,
        customer=make_customer(),
        paid=True,
        source="MOCK",
    )
    data.update(overrides)
    return Order(**data)


class FakeTransport:
    """Transport HTTP finto: registra ogni chiamata, risponde in ordine."""

    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.calls = []

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers),
                "body": body,
                "timeout": timeout,
            }
        )
        if not self.responses:
            return 200, b"{}"
        status, payload = self.responses.pop(0)
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload).encode()
        return status, payload

    def json_body(self, index=-1):
        return json.loads(self.calls[index]["body"].decode())
