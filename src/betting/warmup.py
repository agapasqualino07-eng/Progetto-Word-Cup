"""
Warm-up manager — stake ridotto nelle prime giornate.

Lezione KellyBench: niente all-in al primo giorno. Il sistema "scalda" lo stake
per fase, e nei knockout segnala il cambio di strategia (più Under/Draw).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class Phase:
    nome: str
    stake_factor: float
    nota: str


# Fasi del Mondiale 2026 (date della specifica).
_OSSERVAZIONE = Phase("osservazione", 0.5, "Prime giornate: solo tracking, stake dimezzato")
_CAUTELA = Phase("cautela", 0.8, "Fase 2: stake ridotto")
_NORMALE = Phase("normale", 1.0, "Fase a regime")
_KNOCKOUT = Phase("knockout", 1.0, "Knockout: attenzione, più Under e Draw")


def phase_for(d: date) -> Phase:
    """Restituisce la fase di warm-up per una data."""
    if d < date(2026, 6, 18):
        return _OSSERVAZIONE          # 11–17 giugno (e pre-torneo)
    if d < date(2026, 6, 24):
        return _CAUTELA               # 18–23 giugno
    if d < date(2026, 6, 29):
        return _NORMALE               # 24–28 giugno
    return _KNOCKOUT                  # dal 29 giugno (fase a eliminazione)


def warmup_stake(base_stake: float, d: date) -> float:
    """Applica il fattore di warm-up allo stake base."""
    return round(base_stake * phase_for(d).stake_factor, 2)
