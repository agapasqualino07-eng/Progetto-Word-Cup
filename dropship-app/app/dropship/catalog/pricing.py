"""Pricing con IVA, commissioni di pagamento e margine minimo garantito.

Definizioni (P = prezzo lordo IVA inclusa, v = aliquota IVA):
    netto     = P / (1 + v)
    iva       = P - netto
    fee       = P * fee_pct + fee_fixed
    profitto  = netto - costo_fornitore - spedizione - fee
    margine   = profitto / netto
Il prezzo minimo che garantisce margine m si ottiene risolvendo per P:
    P = (costo + spedizione + fee_fixed) / ((1 - m) / (1 + v) - fee_pct)
ROAS di break-even = P / profitto (spesa ads per vendita = profitto per vendita).
"""

from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from dropship.models import PriceQuote

CENT = Decimal("0.01")


class PricingError(ValueError):
    pass


def _money(x):
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def _validate(cost, shipping):
    if cost is None or cost <= 0:
        raise PricingError("costo fornitore deve essere > 0")
    if shipping is None or shipping < 0:
        raise PricingError("costo spedizione deve essere >= 0")


def min_price(supplier_cost, shipping_cost, cfg):
    _validate(supplier_cost, shipping_cost)
    denom = (1 - cfg.min_margin) / (1 + cfg.vat_rate) - cfg.payment_fee_pct
    if denom <= 0:
        raise PricingError("configurazione impossibile: margine+commissioni >= 100%")
    return (supplier_cost + shipping_cost + cfg.payment_fee_fixed) / denom


def charm_round_up(price):
    """Arrotonda per eccesso a X.90 (mai sotto il prezzo dato)."""
    base = price.to_integral_value(rounding=ROUND_CEILING) - 1
    candidate = base + Decimal("0.90")
    if candidate < price:
        candidate += 1
    return _money(candidate)


def quote_at_price(supplier_cost, shipping_cost, price_gross, cfg, rounding=True):
    _validate(supplier_cost, shipping_cost)
    if price_gross <= 0:
        raise PricingError("prezzo deve essere > 0")
    r = _money if rounding else (lambda x: x)
    net = price_gross / (1 + cfg.vat_rate)
    fees = price_gross * cfg.payment_fee_pct + cfg.payment_fee_fixed
    landed = supplier_cost + shipping_cost
    net_r, fees_r = r(net), r(fees)
    profit = net_r - landed - fees_r
    margin = profit / net_r if net_r > 0 else Decimal("0")
    be = None
    if profit > 0:
        be = (price_gross / profit).quantize(CENT, rounding=ROUND_HALF_UP)
    return PriceQuote(
        price_gross=r(price_gross),
        price_net=net_r,
        vat=r(price_gross - net_r),
        payment_fees=fees_r,
        landed_cost=r(landed),
        profit=r(profit),
        margin=margin,
        break_even_roas=be,
    )


def suggest_price(supplier_cost, shipping_cost, cfg, market_price=None):
    """Prezzo di vendita: quello di mercato se rispetta il margine minimo,
    altrimenti il minimo che lo garantisce (arrotondato a .90 per eccesso)."""
    floor = min_price(supplier_cost, shipping_cost, cfg)
    if market_price is not None and market_price >= floor:
        q = quote_at_price(supplier_cost, shipping_cost, market_price, cfg)
        if q.margin >= cfg.min_margin:
            return q
    price = charm_round_up(floor)
    q = quote_at_price(supplier_cost, shipping_cost, price, cfg)
    # l'arrotondamento dei centesimi può in rari casi limare il margine: ricorreggi
    while q.margin < cfg.min_margin:
        price += 1
        q = quote_at_price(supplier_cost, shipping_cost, price, cfg)
    return q


def margin_at_price(supplier_cost, shipping_cost, price_gross, cfg):
    return quote_at_price(supplier_cost, shipping_cost, price_gross, cfg).margin
