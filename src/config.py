"""
Configurazione centrale — letta da variabili d'ambiente (.env).

Nel sistema completo si usa pydantic-settings; qui usiamo os.environ per
restare senza dipendenze. I parametri di scommessa riflettono le REGOLE
CRITICHE (immutabili) della specifica.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _f(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    # Bankroll e obiettivo.
    initial_bankroll: float = _f("INITIAL_BANKROLL", 100.0)
    target_bankroll: float = _f("TARGET_BANKROLL", 1000.0)

    # Stake.
    stake_floor: float = _f("STAKE_FLOOR", 5.0)
    stake_cap: float = _f("STAKE_CAP", 20.0)

    # Soglie di valore.
    min_edge_single: float = _f("MIN_EDGE_SINGLE", 0.05)

    # Fonti dati / quote.
    odds_api_key: str = os.environ.get("ODDS_API_KEY", "")
    football_api_key: str = os.environ.get("FOOTBALL_API_KEY", "")

    # Infrastruttura (placeholder: il sistema completo li usa per DB/bot/scraper).
    database_url: str = os.environ.get("DATABASE_URL", "")
    redis_url: str = os.environ.get("REDIS_URL", "")
    telegram_token: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.environ.get("TELEGRAM_CHAT_ID", "")
    timezone: str = os.environ.get("TZ", "Europe/Rome")


settings = Settings()
