"""Selezione prodotti: solo candidati che superano trend score E conformità."""

from dataclasses import dataclass
from typing import List, Tuple

from dropship.catalog.pricing import PricingError, suggest_price
from dropship.guardrails.compliance import check_product
from dropship.models import PriceQuote, ProductCandidate, TrendResult


@dataclass(frozen=True)
class SelectedProduct:
    candidate: ProductCandidate
    trend: TrendResult
    quote: PriceQuote


@dataclass(frozen=True)
class SelectionReport:
    selected: Tuple[SelectedProduct, ...]
    rejected: Tuple[Tuple[str, Tuple[str, ...]], ...]


def select_products(results, pricing_cfg, limit=3):
    selected: List[SelectedProduct] = []
    rejected = []
    for r in results:
        sku = r.candidate.sku
        compliance = check_product(r.candidate)
        if not compliance.allowed:
            rejected.append((sku, ("BLOCCATO guardrail",) + compliance.reasons))
            continue
        if not r.passed:
            rejected.append((sku, r.reasons))
            continue
        if len(selected) >= limit:
            rejected.append((sku, (f"oltre il limite di {limit} prodotti",)))
            continue
        try:
            q = suggest_price(r.candidate.supplier_cost, r.candidate.shipping_cost, pricing_cfg, r.market_price)
        except PricingError as exc:
            rejected.append((sku, (f"pricing: {exc}",)))
            continue
        selected.append(SelectedProduct(r.candidate, r, q))
    return SelectionReport(tuple(selected), tuple(rejected))
