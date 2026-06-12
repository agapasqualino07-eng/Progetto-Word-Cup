"""
Entrypoint FastAPI.

Endpoint:
  GET  /                  info
  GET  /health            health check + regole anti-allucinazione
  GET  /piano             piano di giornata da dati MOCK (gira senza chiavi)
  POST /piano/genera      piano da quote fornite nel body (o da The Odds API)

Il sistema completo aggiunge WebSocket, dashboard, bot Telegram, scraper SNAI
e scheduler — vedi README "Roadmap".

Avvio:  uvicorn src.main:app --reload
"""
from __future__ import annotations

from datetime import date

from .anti_hallucination import TRUTH_RULES
from .betting.daily_allocator import DailyAllocator
from .config import settings
from .data.news.collector import NewsCollector
from .data.odds_api import MatchOdds, OddsCollector
from .models.schemas import DailyPlan, Selection
from .services.match_report import build_match_report
from .services.model_provider import get_default_model
from .services.pipeline import build_selections, generate_plan
from .services.serializers import plan_to_dict

try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    from pydantic import BaseModel
except ImportError:  # il core funziona anche senza FastAPI/pydantic
    FastAPI = None  # type: ignore
    BaseModel = object  # type: ignore


def build_plan(
    selections: list[Selection],
    bankroll: float,
    plan_date: date | None = None,
) -> DailyPlan:
    """Incapsula il flusso Selection[] → DailyPlan (riusabile fuori da FastAPI).
    È l'entrypoint documentato in CLAUDE.md e usato da examples/demo_piano."""
    return DailyAllocator().allocate(selections, plan_date or date.today(), bankroll)


def build_plan_from_mock(bankroll: float, plan_date: date | None = None) -> dict:
    """Genera un piano da dati mock e lo serializza. Riusabile fuori da FastAPI."""
    odds = OddsCollector().get_odds(use_mock=True, plan_date=plan_date)
    model, _ = get_default_model()
    plan = generate_plan(odds, bankroll, plan_date or date.today(), model=model)
    return plan_to_dict(plan)


if FastAPI is not None:

    app = FastAPI(title="WorldCupEdge", version="0.2.0")

    class MatchOddsIn(BaseModel):
        match_id: str
        home: str
        away: str
        odds_1: float
        odds_x: float
        odds_2: float
        group: str | None = None
        matchday: int | None = None

    class PianoRequest(BaseModel):
        bankroll: float = settings.initial_bankroll
        partite: list[MatchOddsIn] = []
        usa_odds_api: bool = False  # se True e c'è la chiave, ignora "partite"

    @app.get("/")
    def root() -> dict:
        return {
            "nome": "WorldCupEdge",
            "descrizione": "Ricerca quantitativa — FIFA World Cup 2026",
            "obiettivo": f"€{settings.initial_bankroll:.0f} → €{settings.target_bankroll:.0f}",
            "endpoints": ["/health", "/piano", "/piano/genera"],
        }

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "regole_verita": list(TRUTH_RULES)}

    @app.get("/piano")
    def piano_mock(bankroll: float = settings.initial_bankroll) -> dict:
        """Piano di giornata da dati MOCK — gira senza alcuna chiave."""
        return build_plan_from_mock(bankroll)

    @app.get("/report")
    def report(
        home: str,
        away: str,
        odds_1: float | None = None,
        odds_x: float | None = None,
        odds_2: float | None = None,
        bankroll: float = settings.initial_bankroll,
        news: bool = False,
        news_demo: bool = False,
    ) -> dict:
        """
        Report on-demand di una partita.
        - odds_1/x/2 → aggiunge il consiglio di scommessa.
        - news=true  → aggrega le testate (RSS reali; offline → DATO MANCANTE).
        - news_demo=true → usa news di esempio etichettate (solo dimostrazione).
        """
        odds = None
        if odds_1 and odds_x and odds_2:
            odds = {"1": odds_1, "X": odds_x, "2": odds_2}
        nh = na = None
        if news or news_demo:
            nc = NewsCollector()
            nh = nc.for_team(home, use_mock=news_demo)
            na = nc.for_team(away, use_mock=news_demo)
        model, _ = get_default_model()
        return build_match_report(
            home, away, odds=odds, bankroll=bankroll, news_home=nh, news_away=na,
            model=model,
        ).to_dict()

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard() -> str:
        """Dashboard minimale: partite di oggi + modulo per interrogare una partita."""
        odds = OddsCollector(settings.odds_api_key).get_odds()
        model, _ = get_default_model()
        sels = build_selections(odds, model)
        righe = "".join(
            f"<tr><td>{s.home} - {s.away}</td><td><b>{s.outcome.value}</b></td>"
            f"<td>{s.model_prob:.0%}</td><td>{s.edge:+.1%}</td>"
            f"<td><a href='/report?home={s.home}&away={s.away}"
            f"&odds_1={o.odds_1}&odds_x={o.odds_x}&odds_2={o.odds_2}'>report</a></td></tr>"
            for s, o in zip(sels, odds)
        )
        return f"""<!doctype html><html lang="it"><head><meta charset="utf-8">
<title>WorldCupEdge</title><style>
body{{font-family:system-ui;max-width:760px;margin:24px auto;padding:0 12px}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background:#222;color:#fff}}.box{{background:#f5f5f5;padding:16px;border-radius:8px}}
</style></head><body>
<h1>⚽ WorldCupEdge</h1>
<p>Pronostici di oggi (fonte: {odds[0].source if odds else '—'}).
Tocca <i>report</i> per il dettaglio completo con consiglio di scommessa.</p>
<table><tr><th>Partita</th><th>Esito</th><th>Prob</th><th>Edge</th><th></th></tr>{righe}</table>
<div class="box"><h3>Chiedi una partita qualsiasi</h3>
<form action="/report" method="get">
Casa: <input name="home" value="Argentina"> Ospite: <input name="away" value="Messico"><br><br>
Quota 1: <input name="odds_1" size="4"> X: <input name="odds_x" size="4">
2: <input name="odds_2" size="4"> (opzionali, per il consiglio)<br><br>
<button type="submit">Genera report</button></form></div>
<p style="color:#888">⚠️ Quote da verificare su SNAI. Valore atteso negativo: gioca responsabilmente.</p>
</body></html>"""

    @app.post("/piano/genera")
    def piano_genera(req: PianoRequest) -> dict:
        if req.usa_odds_api:
            odds = OddsCollector(settings.odds_api_key).get_odds()
        else:
            odds = [
                MatchOdds(
                    match_id=p.match_id, home=p.home, away=p.away,
                    odds_1=p.odds_1, odds_x=p.odds_x, odds_2=p.odds_2,
                    source="input", group=p.group, matchday=p.matchday,
                )
                for p in req.partite
            ]
        if not odds:
            return {"errore": "Nessuna partita fornita e nessuna fonte quote attiva."}
        model, _ = get_default_model()
        plan = generate_plan(odds, req.bankroll, date.today(), model=model)
        return plan_to_dict(plan)
