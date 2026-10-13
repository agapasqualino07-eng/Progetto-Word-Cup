"""Sito statico di fallback (quando Shopify non è configurato).

Sicurezza: tutto il testo è escapato, i nomi file derivano da slug [a-z0-9-],
ogni percorso è verificato dentro ``out_dir``, CSP restrittiva (niente script).
"""

import html
from pathlib import Path

from dropship.store.listing import slugify

CSP = "default-src 'none'; img-src https: data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"

PAGE = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<title>{title}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem;color:#222}}
.mock{{background:#fff3cd;border:1px solid #e0c060;padding:.5rem 1rem;border-radius:6px}}
.price{{font-size:1.5rem;font-weight:700}}a{{color:#0b57d0}}</style>
</head>
<body>
{banner}
{body}
<footer><p><small>Prezzi IVA inclusa. Diritto di recesso 14 giorni.</small></p></footer>
</body>
</html>
"""


def _safe_path(out_dir, name):
    out_dir = Path(out_dir).resolve()
    target = (out_dir / name).resolve()
    if not target.is_relative_to(out_dir):
        raise ValueError("percorso fuori dalla cartella del sito")
    return target


def _is_mock(listing):
    return "source:MOCK" in listing["product"].get("tags", "") or "data:MOCK" in listing["product"].get("tags", "")


def _banner(is_mock):
    if not is_mock:
        return ""
    return '<p class="mock">Contenuti e dati di ESEMPIO (MOCK): non sono prodotti o prezzi reali.</p>'


def write_static_site(listings, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    links = []
    any_mock = False
    for listing in listings:
        p = listing["product"]
        is_mock = _is_mock(listing)
        any_mock = any_mock or is_mock
        handle = slugify(p.get("handle") or p.get("title"))
        price = html.escape(str(p["variants"][0]["price"]))
        body = (
            f"<p><a href=\"index.html\">&larr; Catalogo</a></p>"
            f"<h1>{html.escape(p['title'])}</h1>"
            f"<p class=\"price\">&euro; {price}</p>"
            f"{p['body_html']}"  # già escapato in build_listing
        )
        page = PAGE.format(csp=CSP, title=html.escape(p["title"]), banner=_banner(is_mock), body=body)
        target = _safe_path(out_dir, f"{handle}.html")
        target.write_text(page, encoding="utf-8")
        written.append(target)
        links.append(f"<li><a href=\"{html.escape(handle)}.html\">{html.escape(p['title'])}</a> &ndash; &euro; {price}</li>")
    index_body = "<h1>Catalogo</h1><ul>" + "".join(links) + "</ul>"
    index = PAGE.format(csp=CSP, title="Catalogo", banner=_banner(any_mock), body=index_body)
    idx = _safe_path(out_dir, "index.html")
    idx.write_text(index, encoding="utf-8")
    written.append(idx)
    return written
