"""
Bot Telegram — invio del piano e comandi.

L'import di python-telegram-bot è LAZY: il modulo si importa anche senza la
libreria/il token, e in quel caso `send_daily_plan(..., dry_run=True)` stampa
il messaggio a console invece di inviarlo. Così è testabile e dimostrabile
senza credenziali; con token + libreria, invia davvero.

Avvio del bot interattivo (con token):  python -m src.notifications.telegram_bot
"""
from __future__ import annotations

from datetime import date

from ..config import settings
from ..data.odds_api import OddsCollector
from ..models.schemas import DailyPlan
from ..services.match_report import build_match_report
from ..services.pipeline import generate_plan
from .message_formatter import format_daily_plan, format_help
from .telegram_client import CONFIRM_BUTTONS, send_message


def _today_plan(bankroll: float | None = None) -> tuple[DailyPlan, bool, int]:
    """
    Genera il piano di oggi. Ritorna (piano, is_mock, n_partite).
    Senza chiave Odds API i dati sono MOCK (etichettati); con chiave sono reali
    e filtrati alle partite delle prossime ore.
    """
    collector = OddsCollector(settings.odds_api_key)
    odds = collector.get_odds()
    is_mock = bool(odds) and any(o.is_mock for o in odds)
    plan = generate_plan(odds, bankroll or settings.initial_bankroll, date.today())
    return plan, is_mock, len(odds)


def send_daily_plan(
    plan: DailyPlan | None = None,
    dry_run: bool = True,
    token: str | None = None,
    chat_id: str | None = None,
    with_buttons: bool = True,
) -> str:
    """
    Invia (o stampa, in dry-run) il piano di giornata con i pulsanti di conferma.
    Usa il client stdlib: nessuna dipendenza esterna. Ritorna il testo inviato.
    """
    if plan is None:
        plan, is_mock, n_matches = _today_plan()
    else:
        is_mock, n_matches = False, None
    text = format_daily_plan(plan, settings.target_bankroll,
                             is_mock=is_mock, n_matches=n_matches)

    token = token or settings.telegram_token
    chat_id = chat_id or settings.telegram_chat_id
    if dry_run or not token or not chat_id:
        if not dry_run:
            print("[telegram] token/chat_id mancanti → dry-run forzato")
        print(text)
        return text

    send_message(token, chat_id, text,
                 buttons=CONFIRM_BUTTONS if with_buttons else None)
    return text


def run_bot(token: str | None = None) -> None:
    """
    Avvia il bot interattivo con i comandi /oggi /stato /obiettivo /aiuto.
    Richiede python-telegram-bot (v20+) e un token valido.
    """
    token = token or settings.telegram_token
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN mancante: impossibile avviare il bot")

    from telegram import (  # import lazy
        InlineKeyboardButton,
        InlineKeyboardMarkup,
        Update,
    )
    from telegram.ext import (
        Application,
        CallbackQueryHandler,
        CommandHandler,
        ContextTypes,
    )

    def _today_odds(ctx) -> list:
        """Quote di oggi, in cache nella sessione del bot (per i pulsanti report)."""
        odds = ctx.bot_data.get("today_odds")
        if odds is None:
            odds = OddsCollector(settings.odds_api_key).get_odds()
            ctx.bot_data["today_odds"] = odds
        return odds

    def _plan_keyboard(odds: list) -> InlineKeyboardMarkup:
        rows = [[InlineKeyboardButton(f"📊 {o.home}-{o.away}", callback_data=f"rep:{i}")]
                for i, o in enumerate(odds)]
        rows.append([InlineKeyboardButton("✅ Confermo tutto", callback_data="confirm_all"),
                     InlineKeyboardButton("❌ Salto", callback_data="skip_day")])
        return InlineKeyboardMarkup(rows)

    async def oggi(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        odds = _today_odds(ctx)
        is_mock = bool(odds) and any(o.is_mock for o in odds)
        plan = generate_plan(odds, settings.initial_bankroll, date.today())
        await update.message.reply_text(
            format_daily_plan(plan, settings.target_bankroll,
                              is_mock=is_mock, n_matches=len(odds)),
            reply_markup=_plan_keyboard(odds),
        )

    async def partita(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        """/partita Argentina - Messico → report completo."""
        testo = " ".join(ctx.args)
        if "-" not in testo:
            await update.message.reply_text("Usa: /partita Casa - Ospite")
            return
        casa, ospite = (p.strip() for p in testo.split("-", 1))
        rep = build_match_report(casa, ospite, bankroll=settings.initial_bankroll)
        await update.message.reply_text(rep.to_text())

    async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        data = query.data
        if data.startswith("rep:"):
            odds = _today_odds(ctx)
            i = int(data.split(":")[1])
            o = odds[i]
            rep = build_match_report(
                o.home, o.away,
                odds={"1": o.odds_1, "X": o.odds_x, "2": o.odds_2},
                bankroll=settings.initial_bankroll,
            )
            await query.message.reply_text(rep.to_text())
            return
        # NB: la persistenza del portafoglio è in roadmap; qui confermiamo solo.
        risposte = {
            "confirm_all": "✅ Registrate. Piazzale su SNAI. Ti aggiorno alle formazioni.",
            "skip_day": "❌ Nessuna bet registrata oggi. A domani!",
        }
        await query.message.reply_text(risposte.get(data, "Ok."))

    async def stato(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            f"💰 Bankroll iniziale: €{settings.initial_bankroll:.0f} | "
            f"🎯 Obiettivo: €{settings.target_bankroll:.0f}"
        )

    async def aiuto(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(format_help())

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("oggi", oggi))
    app.add_handler(CommandHandler("partita", partita))
    app.add_handler(CommandHandler(["stato", "obiettivo"], stato))
    app.add_handler(CommandHandler(["aiuto", "start", "help"], aiuto))
    app.add_handler(CallbackQueryHandler(on_button))
    print("Bot avviato. Premi Ctrl+C per fermare.")
    app.run_polling()


if __name__ == "__main__":
    run_bot()
