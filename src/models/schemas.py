"""
Modelli dati del dominio (dataclass, zero dipendenze).

Nel sistema completo questi vengono affiancati da schemi Pydantic per il
layer API/DB; qui usiamo dataclass così il core resta testabile senza dipendenze.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from ..anti_hallucination import ConfidenceLevel


class Outcome(str, Enum):
    HOME = "1"
    DRAW = "X"
    AWAY = "2"
    OVER_2_5 = "Over2.5"
    UNDER_2_5 = "Under2.5"


class Phase(str, Enum):
    GROUP = "gironi"
    KNOCKOUT = "knockout"


@dataclass
class Selection:
    """Una singola scelta su una partita: esito + probabilità modello + quota."""
    match_id: str
    home: str
    away: str
    outcome: Outcome
    model_prob: float          # probabilità stimata dal modello [0,1]
    odds: float                # quota offerta dal bookmaker (es. 1.85)
    group: str | None = None   # girone (None nei knockout)
    matchday: int | None = None
    kickoff_date: date | None = None
    phase: Phase = Phase.GROUP
    confederation_home: str | None = None
    confederation_away: str | None = None
    data_completeness: float = 1.0
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIA

    @property
    def implied_prob(self) -> float:
        """Probabilità implicita nella quota (include il margine del book)."""
        return 1.0 / self.odds if self.odds > 0 else 0.0

    @property
    def edge(self) -> float:
        """Vantaggio stimato: prob modello − prob implicita. >0 = valore."""
        return self.model_prob - self.implied_prob


class BetType(str, Enum):
    SINGOLA = "singola"
    DOPPIA = "doppia"
    TRIPLA = "tripla"


@dataclass
class Bet:
    """Scommessa: 1 gamba (singola), 2 (doppia) o 3 (tripla)."""
    bet_type: BetType
    legs: list[Selection]
    stake: float = 0.0

    @property
    def combined_odds(self) -> float:
        odds = 1.0
        for leg in self.legs:
            odds *= leg.odds
        return round(odds, 2)

    @property
    def model_prob(self) -> float:
        """Probabilità che TUTTE le gambe vincano (gambe trattate indipendenti)."""
        p = 1.0
        for leg in self.legs:
            p *= leg.model_prob
        return p

    @property
    def implied_prob(self) -> float:
        p = 1.0
        for leg in self.legs:
            p *= leg.implied_prob
        return p

    @property
    def edge(self) -> float:
        return self.model_prob - self.implied_prob

    @property
    def potential_payout(self) -> float:
        return round(self.stake * self.combined_odds, 2)


@dataclass
class DailyPlan:
    """Il piano di giornata: 4 singole + 4 doppie + 2 triple (quando possibile)."""
    plan_date: date
    bankroll: float
    budget: float
    stake: float
    singole: list[Bet] = field(default_factory=list)
    doppie: list[Bet] = field(default_factory=list)
    triple: list[Bet] = field(default_factory=list)

    @property
    def all_bets(self) -> list[Bet]:
        return [*self.singole, *self.doppie, *self.triple]

    @property
    def total_staked(self) -> float:
        return round(sum(b.stake for b in self.all_bets), 2)
