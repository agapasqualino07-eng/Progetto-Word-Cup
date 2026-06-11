"""
Modello Poisson per il calcio internazionale — gold standard per 1X2/Over.

Stima due intensità di gol (lambda) per le due squadre, costruisce la matrice
dei risultati e ne deriva le probabilità di 1 / X / 2 e Over/Under 2.5.

Implementazione in sola standard library (niente scipy) così è testabile
ovunque. Il sistema completo può sostituire questo con scipy.stats.poisson
e raffinare attack/defense con dati reali (xG, ELO, ranking) — l'interfaccia
resta identica.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..constants import HOSTS, base_attack, base_defense

MAX_GOALS = 8  # troncamento della coda: P(gol > 8) è trascurabile


def poisson_pmf(k: int, lam: float) -> float:
    """P(X = k) per X ~ Poisson(lam)."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * lam**k / math.factorial(k)


@dataclass
class MatchProbabilities:
    prob_1: float       # vittoria casa
    prob_x: float       # pareggio
    prob_2: float       # vittoria trasferta
    over_2_5: float
    under_2_5: float
    lambda_home: float
    lambda_away: float

    def as_dict(self) -> dict[str, float]:
        return {
            "prob_1": self.prob_1,
            "prob_x": self.prob_x,
            "prob_2": self.prob_2,
            "over_2_5": self.over_2_5,
            "under_2_5": self.under_2_5,
            "lambda_home": self.lambda_home,
            "lambda_away": self.lambda_away,
        }


@dataclass
class PoissonModel:
    """
    Rating attack/defense per squadra. Di default si parte dai prior per tier
    (constants), ma si possono iniettare rating calibrati su dati reali.
    """
    attack: dict[str, float] = field(default_factory=dict)
    defense: dict[str, float] = field(default_factory=dict)

    def _attack(self, team: str) -> float:
        return self.attack.get(team, base_attack(team))

    def _defense(self, team: str) -> float:
        return self.defense.get(team, base_defense(team))

    def _home_advantage(self, home: str, venue_country: str | None) -> float:
        """Vantaggio host: pieno se gioca nel proprio paese, ridotto altrove."""
        if home in HOSTS and venue_country == home:
            return 0.25
        if home in HOSTS:
            return 0.10
        return 0.0

    def expected_goals(
        self, home: str, away: str, venue_country: str | None = None
    ) -> tuple[float, float]:
        ha = self._home_advantage(home, venue_country)
        # lambda = attacco proprio + difesa avversaria + vantaggio campo.
        # Convenzione difesa: più NEGATIVA = più forte (concede meno), quindi
        # va SOMMATA: una difesa forte (valore negativo) abbassa il lambda avversario.
        lambda_home = max(0.05, self._attack(home) + self._defense(away) + ha)
        lambda_away = max(0.05, self._attack(away) + self._defense(home))
        return lambda_home, lambda_away

    def predict_match(
        self, home: str, away: str, venue_country: str | None = None
    ) -> MatchProbabilities:
        lambda_home, lambda_away = self.expected_goals(home, away, venue_country)

        home_pmf = [poisson_pmf(i, lambda_home) for i in range(MAX_GOALS + 1)]
        away_pmf = [poisson_pmf(j, lambda_away) for j in range(MAX_GOALS + 1)]

        p1 = px = p2 = 0.0
        over = 0.0
        for i, ph in enumerate(home_pmf):
            for j, pa in enumerate(away_pmf):
                p = ph * pa
                if i > j:
                    p1 += p
                elif i == j:
                    px += p
                else:
                    p2 += p
                if i + j > 2:
                    over += p

        # Rinormalizza per la coda troncata, così le probabilità sommano a 1.
        total = p1 + px + p2
        if total > 0:
            p1, px, p2 = p1 / total, px / total, p2 / total
        over = min(max(over, 0.0), 1.0)

        return MatchProbabilities(
            prob_1=p1,
            prob_x=px,
            prob_2=p2,
            over_2_5=over,
            under_2_5=1.0 - over,
            lambda_home=lambda_home,
            lambda_away=lambda_away,
        )
