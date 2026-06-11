"""
Invio one-shot del piano di oggi.

Pensato per essere lanciato da uno scheduler (GitHub Action / cron):
  python -m src.notifications.send_today

- Con TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID nell'ambiente → invia su Telegram.
- Senza → dry-run (stampa a console). Nessuna dipendenza esterna richiesta.
- Con ODDS_API_KEY → quote reali; senza → dati mock (etichettati).
"""
from __future__ import annotations

from ..config import settings
from .telegram_bot import send_daily_plan


def main() -> None:
    has_creds = bool(settings.telegram_token and settings.telegram_chat_id)
    if not has_creds:
        print("[send_today] credenziali Telegram assenti → dry-run (stampa).")
    send_daily_plan(dry_run=not has_creds)


if __name__ == "__main__":
    main()
