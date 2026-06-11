"""
Pipeline — collega quote, modello e allocatore per produrre il piano.

Flusso:  MatchOdds[]  →  PoissonModel  →  Selection[]  →  DailyAllocator  →  DailyPlan

Per ogni partita sceglie l'esito (1/X/2) con l'edge più alto; sarà poi il
value engine (dentro l'allocatore) a scartare quelli sotto soglia.
"""
from __future__ import annotations

from datetime import date

from ..anti_hallucination import assess_confidence
from ..betting.daily_allocator import DailyAllocator
from ..betting.value_engine import remove_margin
from ..data.odds_api import MatchOdds
from ..ml.calibration import DEFAULT_MODEL_WEIGHT, calibrate_1x2
from ..ml.poisson_model import PoissonModel
from ..models.schemas import DailyPlan, Outcome, Phase, Selection


def selection_from_odds(
    mo: MatchOdds,
    model: PoissonModel,
    venue_country: str | None = "USA",
    data_completeness: float = 0.85,
    model_ml_prob: float | None = None,
    model_weight: float = DEFAULT_MODEL_WEIGHT,
) -> Selection:
    """Costruisce la Selection sull'esito 1/X/2 con edge massimo per la partita."""
    probs = model.predict_match(mo.home, mo.away, venue_country)

    # Calibrazione: avvicina le probabilità del modello al mercato fair (de-vigato).
    market_fair = remove_margin(mo.odds_1, mo.odds_x, mo.odds_2)
    cal = calibrate_1x2(
        {"1": probs.prob_1, "X": probs.prob_x, "2": probs.prob_2},
        market_fair,
        weight=model_weight,
    )

    candidates = [
        (Outcome.HOME, cal["1"], mo.odds_1),
        (Outcome.DRAW, cal["X"], mo.odds_x),
        (Outcome.AWAY, cal["2"], mo.odds_2),
    ]
    # edge = prob calibrata − prob implicita; scegli l'esito col massimo.
    outcome, model_prob, odds = max(
        candidates, key=lambda c: c[1] - (1.0 / c[2] if c[2] else 0.0)
    )

    # Disaccordo coi modelli ML (se forniti) → declassa la fiducia.
    disagreement = abs(model_prob - model_ml_prob) if model_ml_prob is not None else 0.0
    confidence = assess_confidence(data_completeness, disagreement)

    return Selection(
        match_id=mo.match_id,
        home=mo.home,
        away=mo.away,
        outcome=outcome,
        model_prob=model_prob,
        odds=odds,
        group=mo.group,
        matchday=mo.matchday,
        kickoff_date=mo.commence_date,
        phase=Phase.GROUP if mo.matchday is not None else Phase.KNOCKOUT,
        data_completeness=data_completeness,
        confidence=confidence,
    )


def build_selections(
    odds: list[MatchOdds],
    model: PoissonModel | None = None,
    data_completeness: float = 0.85,
) -> list[Selection]:
    model = model or PoissonModel()
    return [selection_from_odds(mo, model, data_completeness=data_completeness)
            for mo in odds]


def generate_plan(
    odds: list[MatchOdds],
    bankroll: float,
    plan_date: date | None = None,
    model: PoissonModel | None = None,
) -> DailyPlan:
    selections = build_selections(odds, model)
    return DailyAllocator().allocate(selections, plan_date or date.today(), bankroll)
