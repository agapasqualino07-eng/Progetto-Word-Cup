"""Costruzione della scheda prodotto nel formato Shopify Admin API (REST products.json).

Ogni testo proveniente da fornitore o LLM viene ESCAPATO prima di finire in HTML.
"""

import html
import re
import unicodedata


def slugify(text):
    text = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:80].strip("-") or "prodotto"


def render_body_html(copy):
    parts = [f"<p>{html.escape(copy.description)}</p>"]
    if copy.bullets:
        items = "".join(f"<li>{html.escape(b)}</li>" for b in copy.bullets)
        parts.append(f"<ul>{items}</ul>")
    return "".join(parts)


def build_listing(candidate, quote, copy, status="draft"):
    if status not in ("draft", "active"):
        raise ValueError("status deve essere draft o active")
    return {
        "product": {
            "title": copy.title[:255],
            "handle": slugify(copy.title),
            "body_html": render_body_html(copy),
            "vendor": "Dropship MVP",
            "product_type": candidate.category,
            "status": status,
            "tags": ", ".join([candidate.keyword, f"source:{copy.source}", f"data:{candidate.source}"]),
            "variants": [
                {
                    "sku": candidate.sku,
                    "price": str(quote.price_gross),
                    "taxable": True,
                    "requires_shipping": True,
                    "weight": candidate.weight_kg,
                    "weight_unit": "kg",
                    "inventory_management": None,
                }
            ],
        }
    }
