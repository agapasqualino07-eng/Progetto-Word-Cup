"""
Calibrazione delle probabilità — shrinkage verso il mercato.

Il Poisson a prior grezzi è SPESSO troppo sicuro, soprattutto sugli underdog:
trova "valore" dove non c'è. La contromisura onesta è la regolarizzazione verso
il mercato: la probabilità calibrata è una media pesata tra modello e quota
"de-vigata" (senza margine del book). Riduce gli edge spuri e l'overconfidence
(lezione KellyBench), in attesa dell'ensemble ML calibrato (ECE < 0.05).

  calibrata = w · modello + (1 − w) · mercato_fair

w alto = ci si fida del modello; w basso = ci si fida del mercato.
"""
from __future__ import annotations

# Peso di default sul modello. 0.5 = metà modello, metà mercato (prudente).
DEFAULT_MODEL_WEIGHT = 0.5


def shrink_to_market(
    model_prob: float, market_fair_prob: float, weight: float = DEFAULT_MODEL_WEIGHT
) -> float:
    """Media pesata tra probabilità del modello e probabilità fair di mercato."""
    weight = min(max(weight, 0.0), 1.0)
    return weight * model_prob + (1.0 - weight) * market_fair_prob


def calibrate_1x2(
    model: dict[str, float],
    market_fair: dict[str, float],
    weight: float = DEFAULT_MODEL_WEIGHT,
) -> dict[str, float]:
    """
    Calibra un mercato 1X2 e rinormalizza così le probabilità sommano a 1.
    `model` e `market_fair` hanno chiavi "1"/"X"/"2".
    """
    blended = {
        k: shrink_to_market(model.get(k, 0.0), market_fair.get(k, 0.0), weight)
        for k in ("1", "X", "2")
    }
    total = sum(blended.values())
    if total <= 0:
        return blended
    return {k: v / total for k, v in blended.items()}
