"""
Formattatore messaggi Telegram (funzioni pure, zero dipendenze, testabili).

Tiene la logica di presentazione separata dal trasporto (il bot): così si può
testare il testo senza una connessione Telegram.
"""
from __future__ import annotations

from ..anti_hallucination import VERIFY_ODDS, is_betable
from ..betting.value_engine import MIN_EDGE_SINGLE
from ..models.schemas import Bet, DailyPlan, Selection

_LINE = "━" * 28


def _legs(bet: Bet) -> str:
    return " + ".join(f"{leg.home} ({leg.outcome.value})" for leg in bet.legs)


def _skip_reason(s: Selection) -> str:
    """Spiega in una riga perché una partita è stata saltata (trasparenza)."""
    if not is_betable(s.confidence, s.data_completeness):
        return "dati insufficienti"
    if s.edge < MIN_EDGE_SINGLE:
        return f"edge {s.edge:+.1%} < 5% → nessun valore"
    return "non selezionata (priorità ad altre)"


def format_daily_plan(
    plan: DailyPlan,
    target_bankroll: float = 1000.0,
    is_mock: bool = False,
    n_matches: int | None = None,
) -> str:
    """
    Report mattutino: le bet del giorno + stima EV.

    `is_mock=True`   → antepone un avviso: i dati NON sono reali (manca la chiave).
    `n_matches==0`   → segnala che oggi non ci sono partite in finestra (24-30h),
                       invece del messaggio "nessuna bet di valore".
    """
    progresso = min(plan.bankroll / target_bankroll, 1.0) if target_bankroll else 0.0
    lines = [_LINE]
    if is_mock:
        lines += [
            "⚠️ DATI DI ESEMPIO — queste NON sono partite reali.",
            "   Per le partite vere serve la chiave ODDS_API_KEY (vedi guida).",
            "",
        ]
    lines += [
        f"☀️ PIANO DI GIOCO — {plan.plan_date:%d/%m/%Y}",
        "",
        f"💰 Bankroll: €{plan.bankroll:.2f} | 🎯 Obiettivo: €{target_bankroll:.0f}",
        f"📊 Budget oggi: €{plan.budget:.2f} | Stake: €{plan.stake:.2f}",
        f"📈 Progresso: {progresso:.1%}",
    ]

    if n_matches == 0 and not is_mock:
        lines += [
            "",
            "📅 Nessuna partita in programma nelle prossime ore.",
            "   Nessuna bet oggi: a domani.",
            _LINE,
        ]
        return "\n".join(lines)

    lines += ["", f"═══ LE TUE {len(plan.all_bets)} BET DI OGGI ═══"]

    if plan.singole:
        lines.append("\n🎯 SINGOLE")
        for i, b in enumerate(plan.singole, 1):
            s = b.legs[0]
            lines.append(
                f"  {i}. {s.home} - {s.away} → {s.outcome.value} @ {s.odds} "
                f"(edge {s.edge:+.1%}) — €{b.stake:.2f}"
            )
    if plan.doppie:
        lines.append("\n🎫 DOPPIE")
        for i, b in enumerate(plan.doppie, 1):
            lines.append(f"  {i}. {_legs(b)} @ {b.combined_odds} "
                         f"(edge {b.edge:+.1%}) — €{b.stake:.2f}")
    if plan.triple:
        lines.append("\n🎰 TRIPLE")
        for i, b in enumerate(plan.triple, 1):
            lines.append(f"  {i}. {_legs(b)} @ {b.combined_odds} "
                         f"(edge {b.edge:+.1%}) — €{b.stake:.2f}")

    if not plan.all_bets:
        lines.append("\n⚠️ Nessuna bet di valore oggi. Si salta (edge < 5%).")

    # Trasparenza: partite di oggi valutate ma SENZA bet (così sai che il
    # sistema le ha viste e perché le ha saltate).
    skipped = plan.skipped
    if skipped:
        lines.append("\n📋 Altre partite di oggi (nessuna bet):")
        for s in skipped:
            lines.append(f"  • {s.home} - {s.away}: {_skip_reason(s)}")

    lines += ["", f"📊 Totale puntato: €{plan.total_staked:.2f}",
              f"⚠️ Quote: {VERIFY_ODDS} prima di piazzare.", _LINE]
    return "\n".join(lines)


def format_result_report(
    results: list[tuple[str, bool, float]],
    new_bankroll: float,
    target_bankroll: float = 1000.0,
    plan_date=None,
) -> str:
    """
    Report serale del P&L.
    `results`: lista di (descrizione, vinta?, profitto) per ogni bet regolata.
    """
    vinte = sum(1 for _, won, _ in results if won)
    profitto = sum(p for _, _, p in results)
    progresso = min(new_bankroll / target_bankroll, 1.0) if target_bankroll else 0.0
    intestazione = f"🌙 RISULTATI — {plan_date:%d/%m/%Y}" if plan_date else "🌙 RISULTATI"

    lines = [_LINE, intestazione, ""]
    for descr, won, profit in results:
        lines.append(f"  {'✅' if won else '❌'} {descr} ({profit:+.2f}€)")
    lines += [
        "",
        f"═══ BILANCIO ═══",
        f"🎯 Bet vinte: {vinte}/{len(results)}",
        f"💰 Profitto giornata: €{profitto:+.2f}",
        f"📊 Bankroll: €{new_bankroll:.2f}",
        f"📈 Obiettivo €{target_bankroll:.0f}: {progresso:.1%}",
        _LINE,
    ]
    return "\n".join(lines)


def format_help() -> str:
    return "\n".join([
        "Comandi disponibili:",
        "/oggi — piano delle bet di oggi (con pulsanti report per partita)",
        "/partita Casa - Ospite — report completo di una partita",
        "/stato — bankroll, ROI, obiettivo",
        "/obiettivo — progresso verso €1.000",
        "/aiuto — questo messaggio",
    ])
