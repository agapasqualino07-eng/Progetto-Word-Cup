"""
Daily allocator — il cuore del sistema: allocazione 4-4-2.

Ogni giorno con >=4 partite il budget si divide in 10 bet:
  4 SINGOLE (40%) · 4 DOPPIE (40%) · 2 TRIPLE (20%).
Con meno partite il piano si adatta (non si fabbricano bet inesistenti) e il
budget non usato resta nel bankroll per i giorni successivi.

Reinvestimento: lo stake si adatta al bankroll corrente (compound).
"""
from __future__ import annotations

from datetime import date
from itertools import combinations

from ..anti_hallucination import confidence_score, is_betable
from ..models.schemas import Bet, BetType, DailyPlan, Selection
from .correlation_matrix import (
    MAX_CORRELATION_DOPPIA,
    MAX_CORRELATION_TRIPLA,
    can_combine,
    is_forbidden_pair,
)
from .risk_manager import clamp_stake
from .value_engine import MIN_EDGE_COMBO_LEG, has_value

# Piano per numero di partite disponibili nel giorno.
ALLOCATION_BY_MATCHES: dict[int, dict] = {
    1: {"singole": 1, "doppie": 0, "triple": 0, "budget_pct": 0.10},
    2: {"singole": 2, "doppie": 1, "triple": 0, "budget_pct": 0.30},
    3: {"singole": 3, "doppie": 2, "triple": 1, "budget_pct": 0.60},
    4: {"singole": 4, "doppie": 4, "triple": 2, "budget_pct": 1.00},
}

# Edge combinato minimo per ammettere una doppia / tripla.
MIN_EDGE_DOPPIA = 0.04
MIN_EDGE_TRIPLA = 0.06


def get_daily_plan_params(n_matches: int, bankroll: float) -> dict:
    """
    Calcola budget e stake del giorno dal numero di partite e dal bankroll.
    Lo stake è clampato (floor 5, cap 20). Il budget non usato resta a bankroll.
    """
    plan = ALLOCATION_BY_MATCHES[min(max(n_matches, 1), 4)]
    budget = bankroll * plan["budget_pct"]
    n_total = plan["singole"] + plan["doppie"] + plan["triple"]
    stake = clamp_stake(budget / n_total) if n_total else 0.0
    return {**plan, "n_total": n_total, "budget": round(budget, 2), "stake": stake}


def _rank_key(s: Selection) -> float:
    """Ordina per sicurezza × edge: prima le scelte solide e con valore."""
    return confidence_score(s.confidence) * s.edge


class DailyAllocator:
    """Decide quali match vanno in singole, doppie e triple."""

    def allocate(
        self,
        selections: list[Selection],
        plan_date: date,
        bankroll: float,
    ) -> DailyPlan:
        # 1. Tieni solo selezioni scommettibili (dati sufficienti) e di valore.
        pool = [
            s
            for s in selections
            if is_betable(s.confidence, s.data_completeness) and has_value(s)
        ]
        pool.sort(key=_rank_key, reverse=True)

        n_matches = len({s.match_id for s in pool})
        params = get_daily_plan_params(n_matches, bankroll)
        stake = params["stake"]

        # 2. Le migliori → SINGOLE.
        singole_sel = pool[: params["singole"]]
        singole = [Bet(BetType.SINGOLA, [s], stake) for s in singole_sel]

        # 3. Materiale per combo: una sola selezione per match (no auto-combinazioni).
        combo_pool = self._one_per_match(
            [s for s in pool if s.edge >= MIN_EDGE_COMBO_LEG]
        )

        doppie = self._build_combos(
            combo_pool, size=2, n=params["doppie"], stake=stake,
            max_corr=MAX_CORRELATION_DOPPIA, min_edge=MIN_EDGE_DOPPIA,
            bet_type=BetType.DOPPIA,
        )
        triple = self._build_combos(
            combo_pool, size=3, n=params["triple"], stake=stake,
            max_corr=MAX_CORRELATION_TRIPLA, min_edge=MIN_EDGE_TRIPLA,
            bet_type=BetType.TRIPLA,
        )

        return DailyPlan(
            plan_date=plan_date,
            bankroll=round(bankroll, 2),
            budget=params["budget"],
            stake=stake,
            singole=singole,
            doppie=doppie,
            triple=triple,
        )

    @staticmethod
    def _one_per_match(selections: list[Selection]) -> list[Selection]:
        seen: set[str] = set()
        out: list[Selection] = []
        for s in selections:
            if s.match_id not in seen:
                seen.add(s.match_id)
                out.append(s)
        return out

    @staticmethod
    def _build_combos(
        pool: list[Selection],
        size: int,
        n: int,
        stake: float,
        max_corr: float,
        min_edge: float,
        bet_type: BetType,
    ) -> list[Bet]:
        if n <= 0 or len(pool) < size:
            return []
        candidates: list[Bet] = []
        for combo in combinations(pool, size):
            legs = list(combo)
            # Vietato: stesso girone 3ª giornata, in qualsiasi coppia.
            if any(
                is_forbidden_pair(a, b)
                for a, b in combinations(legs, 2)
            ):
                continue
            if not can_combine(legs, max_corr):
                continue
            bet = Bet(bet_type, legs, stake)
            if bet.edge >= min_edge:
                candidates.append(bet)
        # Le migliori `n` combo per edge combinato. Un match può comparire in
        # più combo (come da specifica): è la stessa selezione di valore
        # ricombinata, non una nuova scommessa sullo stesso esito.
        candidates.sort(key=lambda b: b.edge, reverse=True)
        return candidates[:n]
