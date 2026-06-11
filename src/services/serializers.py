"""Serializzazione dei modelli dominio in dict JSON-friendly (per l'API)."""
from __future__ import annotations

from ..models.schemas import Bet, DailyPlan, Selection


def selection_to_dict(s: Selection) -> dict:
    return {
        "match_id": s.match_id,
        "partita": f"{s.home} - {s.away}",
        "esito": s.outcome.value,
        "prob_modello": round(s.model_prob, 4),
        "prob_implicita": round(s.implied_prob, 4),
        "quota": s.odds,
        "edge": round(s.edge, 4),
        "sicurezza": s.confidence.value,
        "girone": s.group,
        "giornata": s.matchday,
    }


def bet_to_dict(b: Bet) -> dict:
    return {
        "tipo": b.bet_type.value,
        "gambe": [selection_to_dict(leg) for leg in b.legs],
        "quota_totale": b.combined_odds,
        "edge": round(b.edge, 4),
        "stake": b.stake,
        "vincita_potenziale": b.potential_payout,
    }


def plan_to_dict(p: DailyPlan) -> dict:
    return {
        "data": p.plan_date.isoformat(),
        "bankroll": p.bankroll,
        "budget": p.budget,
        "stake": p.stake,
        "n_bet": len(p.all_bets),
        "totale_puntato": p.total_staked,
        "singole": [bet_to_dict(b) for b in p.singole],
        "doppie": [bet_to_dict(b) for b in p.doppie],
        "triple": [bet_to_dict(b) for b in p.triple],
    }
