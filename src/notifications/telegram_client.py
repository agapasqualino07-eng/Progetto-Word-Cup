"""
Client Telegram minimale — solo standard library (urllib).

Invia messaggi via Bot API senza dipendenze: funziona ovunque ci sia Python
(il tuo PC, un GitHub Action, questo container). La parte interattiva avanzata
(gestione dei click sui pulsanti) resta in `telegram_bot.run_bot` con
python-telegram-bot; per il piano mattutino basta questo.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

API_BASE = "https://api.telegram.org"

# Pulsanti di conferma del piano (rule 7: il portafoglio si aggiorna SOLO su conferma).
CONFIRM_BUTTONS = [
    ("✅ Confermo tutto", "confirm_all"),
    ("🔀 Modifico", "edit"),
    ("❌ Oggi salto", "skip_day"),
]


def build_send_payload(
    chat_id: str | int,
    text: str,
    buttons: list[tuple[str, str]] | None = None,
) -> dict:
    """Costruisce il body JSON di sendMessage (funzione pura, testabile)."""
    payload: dict = {"chat_id": chat_id, "text": text}
    if buttons:
        payload["reply_markup"] = {
            "inline_keyboard": [[{"text": label, "callback_data": data}]
                                for label, data in buttons]
        }
    return payload


def send_message(
    token: str,
    chat_id: str | int,
    text: str,
    buttons: list[tuple[str, str]] | None = None,
    timeout: int = 15,
) -> dict:
    """Invia un messaggio. Ritorna la risposta dell'API. Solleva su errore."""
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID mancanti")
    url = f"{API_BASE}/bot{token}/sendMessage"
    data = json.dumps(build_send_payload(chat_id, text, buttons)).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:200]
        raise RuntimeError(f"Telegram API errore {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Telegram non raggiungibile: {exc}") from exc


def get_chat_id_hint(token: str) -> str:
    """URL da aprire nel browser (anche da telefono) per leggere il proprio chat_id."""
    return f"{API_BASE}/bot{token}/getUpdates"
