"""Pubblicazione prodotto con guardrail.

Ordine dei controlli: kill switch -> conformità prodotto -> genera testi ->
conformità testi -> approvazione umana -> pubblicazione.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from dropship.guardrails.approvals import PUBLISH_PRODUCT
from dropship.guardrails.compliance import check_copy, check_product
from dropship.store.listing import build_listing


@dataclass
class PublishOutcome:
    sku: str
    status: str  # PENDING_APPROVAL | PUBLISHED | BLOCKED
    reasons: Tuple[str, ...] = ()
    request_id: Optional[str] = None
    product_id: Optional[str] = None
    listing: Optional[dict] = None
    source: Optional[str] = None


def publish_product(candidate, quote, copywriter, store, approvals, kill_switch):
    kill_switch.assert_inactive("pubblicazione prodotto")

    compliance = check_product(candidate)
    if not compliance.allowed:
        return PublishOutcome(candidate.sku, "BLOCKED", compliance.reasons)

    copy = copywriter.generate(candidate, quote)
    copy_check = check_copy(" ".join([copy.title, copy.description, *copy.bullets]))
    if not copy_check.allowed:
        return PublishOutcome(candidate.sku, "BLOCKED", copy_check.reasons)

    if not approvals.is_approved(PUBLISH_PRODUCT, candidate.sku):
        req = approvals.request(
            PUBLISH_PRODUCT, candidate.sku,
            f"Pubblica '{candidate.title}' a € {quote.price_gross} (margine {quote.margin:.0%})",
        )
        draft = build_listing(candidate, quote, copy, status="draft")
        return PublishOutcome(candidate.sku, "PENDING_APPROVAL", (), req.request_id, listing=draft)

    listing = build_listing(candidate, quote, copy, status="active")
    result = store.publish(listing)
    approvals.consume(PUBLISH_PRODUCT, candidate.sku)
    return PublishOutcome(
        candidate.sku, "PUBLISHED", (), product_id=result.product_id, listing=listing, source=result.source
    )
