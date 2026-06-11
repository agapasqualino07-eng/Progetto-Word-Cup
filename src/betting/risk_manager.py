"""
Risk manager — adattamento dinamico dello stake.

Due meccanismi:
  1. AdaptiveConfidence: riduce la size dopo una striscia negativa, la rialza
     (con cap) dopo una positiva. Contromisura al "no adattamento" di KellyBench.
  2. clamp_stake: applica floor e cap allo stake, così un bankroll esploso o
     prosciugato non porta a puntate assurde.
"""
from __future__ import annotations

from dataclasses import dataclass

# Limiti di stake per singola bet (in euro).
STAKE_FLOOR = 5.0
STAKE_CAP = 20.0


def clamp_stake(stake: float) -> float:
    """Vincola lo stake tra floor e cap."""
    return round(max(STAKE_FLOOR, min(STAKE_CAP, stake)), 2)


@dataclass
class AdaptiveConfidence:
    """
    Fattore moltiplicativo [0.25, 1.2] applicato allo stake in base alla
    striscia di risultati. Si ricalibra a ogni bet conclusa.
    """
    streak: int = 0          # >0 vincente, <0 perdente
    factor: float = 1.0

    def update(self, won: bool) -> float:
        # Aggiorna la striscia.
        if won:
            self.streak = self.streak + 1 if self.streak >= 0 else 1
        else:
            self.streak = self.streak - 1 if self.streak <= 0 else -1

        # Adatta il fattore in base alla striscia corrente.
        if self.streak <= -5:
            self.factor = 0.25
        elif self.streak <= -3:
            self.factor = 0.5
        elif self.streak >= 3:
            self.factor = min(1.2, self.factor + 0.1)
        else:
            # Ritorno graduale verso 1.0 in assenza di strisce forti.
            if self.factor < 1.0:
                self.factor = min(1.0, self.factor + 0.1)
            elif self.factor > 1.0:
                self.factor = max(1.0, self.factor - 0.1)
        self.factor = round(self.factor, 2)
        return self.factor

    def adjusted_stake(self, base_stake: float) -> float:
        return clamp_stake(base_stake * self.factor)
