"""Modelli di dominio (dataclass, nessuna dipendenza esterna)."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, Tuple

MOCK = "MOCK"
MISSING = "DATO MANCANTE"


@dataclass(frozen=True)
class ProductCandidate:
    sku: str
    title: str
    category: str
    supplier_cost: Decimal
    shipping_cost: Decimal
    weight_kg: float
    keyword: str
    source: str
    market_price: Optional[Decimal] = None  # prezzo lordo osservato sul mercato
    description: str = ""
    certifications: Tuple[str, ...] = ()
    brand: Optional[str] = None
    brand_authorized: bool = False
    image_url: str = ""


@dataclass(frozen=True)
class TrendSignal:
    sku: str
    demand_growth: Optional[float]  # es. 0.4 = +40%
    ad_saturation: Optional[float]  # 0..1
    seasonality: Optional[float]  # 0..1, aderenza al periodo corrente
    source: str


@dataclass(frozen=True)
class TrendResult:
    candidate: ProductCandidate
    signal: TrendSignal
    score: float
    passed: bool
    reasons: Tuple[str, ...]
    estimated_margin: Optional[float]


@dataclass(frozen=True)
class PriceQuote:
    price_gross: Decimal
    price_net: Decimal
    vat: Decimal
    payment_fees: Decimal
    landed_cost: Decimal
    profit: Decimal
    margin: Decimal
    break_even_roas: Optional[Decimal]


@dataclass(frozen=True)
class ProductCopy:
    title: str
    description: str
    bullets: Tuple[str, ...]
    source: str


def _mask(text):
    text = str(text or "")
    return (text[:1] + "***") if text else ""


@dataclass(frozen=True)
class Customer:
    name: str
    address_line: str
    city: str
    postal_code: str
    country: str  # ISO 3166-1 alpha-2
    email: str = ""

    def __repr__(self):  # niente PII nei log
        return f"Customer(name={_mask(self.name)!r}, country={self.country!r})"


@dataclass
class Order:
    order_id: str
    sku: str
    quantity: int
    customer: Customer
    paid: bool
    source: str
    status: str = "NEW"
    supplier_order_id: Optional[str] = None


@dataclass(frozen=True)
class SupplierOrder:
    supplier_order_id: str
    status: str
    source: str


@dataclass(frozen=True)
class Tracking:
    tracking_number: Optional[str]
    carrier: str
    status: str
    source: str


@dataclass
class Campaign:
    campaign_id: str
    sku: str
    platform: str
    daily_budget: Decimal
    break_even_roas: Optional[Decimal]
    source: str
    status: str = "PAUSED"  # PAUSED | ACTIVE | STOPPED
    external_id: Optional[str] = None


@dataclass(frozen=True)
class AdMetrics:
    spend: Decimal
    revenue: Decimal
    source: str


@dataclass(frozen=True)
class PublishResult:
    product_id: str
    status: str
    source: str


@dataclass
class ActionOutcome:
    """Esito generico di un'azione soggetta a guardrail."""

    status: str
    reasons: Tuple[str, ...] = ()
    request_id: Optional[str] = None
    extra: dict = field(default_factory=dict)
