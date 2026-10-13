"""Trend score 0..100 + soglie bloccanti configurabili.

Componenti (pesi):
- crescita domanda   30%  (saturazione a +100%)
- saturazione ads    20%  (1 - saturazione)
- margine stimato    25%  (al prezzo di mercato; pieno a 60%)
- peso/spedizione    10%  (0 kg = 1, 2x peso massimo = 0)
- stagionalità       15%  (se assente: neutra 0.5, segnalata)
Soglie: un candidato che viola una soglia NON passa, qualunque sia lo score.
Dati mancanti obbligatori (crescita, saturazione, prezzo di mercato) => non passa.
"""

from dropship.catalog.pricing import PricingError, margin_at_price
from dropship.models import MISSING, TrendResult

WEIGHTS = {"growth": 0.30, "saturation": 0.20, "margin": 0.25, "shipping": 0.10, "season": 0.15}


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def score_candidate(candidate, signal, thresholds, pricing_cfg, market_price=None):
    reasons = []
    passed = True

    price = market_price if market_price is not None else candidate.market_price
    margin = None
    if price is None:
        passed = False
        reasons.append(f"prezzo di mercato: {MISSING}")
    else:
        try:
            margin = float(margin_at_price(candidate.supplier_cost, candidate.shipping_cost, price, pricing_cfg))
        except PricingError as exc:
            passed = False
            reasons.append(f"pricing non valido: {exc}")

    g, s, season = signal.demand_growth, signal.ad_saturation, signal.seasonality
    if g is None:
        passed = False
        reasons.append(f"crescita domanda: {MISSING}")
    elif g < thresholds.min_demand_growth:
        passed = False
        reasons.append(f"crescita domanda {g:.0%} sotto soglia {thresholds.min_demand_growth:.0%}")
    if s is None:
        passed = False
        reasons.append(f"saturazione ads: {MISSING}")
    elif s > thresholds.max_ad_saturation:
        passed = False
        reasons.append(f"saturazione ads {s:.0%} sopra soglia {thresholds.max_ad_saturation:.0%}")
    if margin is not None and margin < thresholds.min_margin:
        passed = False
        reasons.append(f"margine stimato {margin:.0%} sotto soglia {thresholds.min_margin:.0%}")
    if candidate.weight_kg > thresholds.max_weight_kg:
        passed = False
        reasons.append(f"peso {candidate.weight_kg} kg oltre soglia {thresholds.max_weight_kg} kg")
    if season is None:
        reasons.append(f"stagionalità: {MISSING} (considerata neutra)")

    parts = {
        "growth": _clamp(g) if g is not None else 0.0,
        "saturation": 1 - _clamp(s) if s is not None else 0.0,
        "margin": _clamp(margin / 0.6) if margin is not None else 0.0,
        "shipping": _clamp(1 - candidate.weight_kg / (2 * thresholds.max_weight_kg)),
        "season": _clamp(season) if season is not None else 0.5,
    }
    score = round(100 * sum(WEIGHTS[k] * v for k, v in parts.items()), 1)
    if passed and score < thresholds.min_score:
        passed = False
        reasons.append(f"score {score} sotto soglia {thresholds.min_score}")

    return TrendResult(
        candidate=candidate, signal=signal, score=score, passed=passed,
        reasons=tuple(reasons), estimated_margin=margin, market_price=price,
    )


def rank(results):
    return sorted(results, key=lambda r: (not r.passed, -r.score))
