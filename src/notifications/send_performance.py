"""
Invio one-shot del report prestazioni (scoreboard su partite reali giocate).

  python -m src.notifications.send_performance

Con TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID → invia; senza → stampa (dry-run).
Usa il modello con rating FIFA reali se disponibili. Nessuna dipendenza esterna.
"""
from __future__ import annotations

from ..config import settings
from ..services.model_provider import get_default_model
from ..services.performance import build_report
from .telegram_client import send_message


def main() -> None:
    model, _ = get_default_model()
    report = build_report(model)
    if report is None:
        print("[performance] nessuna partita conclusa: niente report.")
        return

    token, chat_id = settings.telegram_token, settings.telegram_chat_id
    if not token or not chat_id:
        print("[performance] credenziali Telegram assenti → dry-run (stampa).")
        print(report)
        return
    send_message(token, chat_id, report)
    print("[performance] report inviato.")


if __name__ == "__main__":
    main()
