"""Scansione: fornitore -> candidati -> segnali -> score -> classifica."""

from dropship.trends.scoring import rank, score_candidate


def scan(supplier, trend_source, keywords, thresholds, pricing_cfg):
    seen = {}
    for kw in keywords:
        for c in supplier.search_products(kw):
            seen.setdefault(c.sku, c)
    results = []
    for c in seen.values():
        signal = trend_source.get_signal(c)
        market = c.market_price if c.market_price is not None else trend_source.market_price(c)
        results.append(score_candidate(c, signal, thresholds, pricing_cfg, market_price=market))
    return rank(results)
