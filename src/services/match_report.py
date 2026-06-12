"""
Report on-demand per singola partita.

Dato `casa` e `ospite` (e opzionalmente le quote 1X2), produce un report
completo: pronostico del modello, probabilità, fattori contestuali e — se ci
sono le quote — il consiglio se scommettere o no (con edge, stake e motivo).

Onestà: senza quote NON si dà un consiglio di scommessa (serve il prezzo di
mercato per misurare il valore) → si indica `VERIFICA SU SNAI`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from ..anti_hallucination import (
    VERIFY_ODDS,
    assess_confidence,
    confidence_score,
    is_betable,
)
from ..betting.value_engine import MIN_EDGE_SINGLE, remove_margin
from ..betting.warmup import warmup_stake
from ..config import settings
from ..constants import (
    DEBUTANTS,
    DEFENDING_CHAMPION,
    HOSTS,
    TEAM_TIERS,
    WORLD_CUP_TRENDS,
    group_of,
)
from ..data.news.collector import NewsItem
from ..data.news.sentiment import analyze
from ..features.news_features import has_injury_news, morale_delta, team_sentiment
from ..ml.calibration import calibrate_1x2
from ..ml.poisson_model import PoissonModel

_OUTCOME_LABEL = {"1": "vittoria casa", "X": "pareggio", "2": "vittoria trasferta"}


@dataclass
class MatchReport:
    home: str
    away: str
    venue_country: str | None
    lambda_home: float
    lambda_away: float
    prob_1: float
    prob_x: float
    prob_2: float
    over_2_5: float
    under_2_5: float
    pronostico: str                 # "1" | "X" | "2" — esito più probabile
    pronostico_prob: float
    notes: list[str] = field(default_factory=list)
    # Campi presenti solo se sono state fornite le quote:
    has_odds: bool = False
    odds: dict[str, float] | None = None
    bet_outcome: str | None = None  # esito su cui valutare la scommessa (max edge)
    edge: float | None = None
    implied_prob: float | None = None
    confidenza: str | None = None
    consiglio: str | None = None    # "SCOMMETTI" | "NON SCOMMETTERE"
    stake_consigliato: float | None = None
    motivo: str | None = None
    news_morale_delta: float | None = None

    def to_dict(self) -> dict:
        d = {
            "partita": f"{self.home} - {self.away}",
            "sede": self.venue_country,
            "gol_attesi": {"casa": round(self.lambda_home, 2),
                           "trasferta": round(self.lambda_away, 2)},
            "probabilita": {"1": round(self.prob_1, 3), "X": round(self.prob_x, 3),
                            "2": round(self.prob_2, 3),
                            "over_2_5": round(self.over_2_5, 3),
                            "under_2_5": round(self.under_2_5, 3)},
            "pronostico": self.pronostico,
            "pronostico_prob": round(self.pronostico_prob, 3),
            "note": self.notes,
            "news_morale_delta": self.news_morale_delta,
            "scommessa": None,
        }
        if self.has_odds:
            d["scommessa"] = {
                "esito_consigliato": self.bet_outcome,
                "quote": self.odds,
                "edge": round(self.edge or 0, 4),
                "prob_implicita": round(self.implied_prob or 0, 4),
                "confidenza": self.confidenza,
                "consiglio": self.consiglio,
                "stake_consigliato": self.stake_consigliato,
                "motivo": self.motivo,
            }
        return d

    def to_text(self) -> str:
        """Formato leggibile per Telegram."""
        line = "━" * 26
        out = [
            line,
            f"📊 {self.home} - {self.away}",
            f"⚽ Gol attesi: {self.lambda_home:.2f} - {self.lambda_away:.2f}",
            "",
            f"  1 ({self.home}): {self.prob_1:.0%}",
            f"  X (pareggio):   {self.prob_x:.0%}",
            f"  2 ({self.away}): {self.prob_2:.0%}",
            f"  Over 2.5: {self.over_2_5:.0%} | Under 2.5: {self.under_2_5:.0%}",
            "",
            f"🎯 Pronostico: {self.pronostico} "
            f"({_OUTCOME_LABEL[self.pronostico]}) — {self.pronostico_prob:.0%}",
        ]
        if self.notes:
            out += ["", "📌 Fattori:"] + [f"  • {n}" for n in self.notes]
        out.append("")
        if self.has_odds:
            icona = "✅" if self.consiglio == "SCOMMETTI" else "❌"
            out += [
                "💶 SCOMMESSA",
                f"  Esito valutato: {self.bet_outcome} "
                f"({_OUTCOME_LABEL[self.bet_outcome]}) @ {self.odds[self.bet_outcome]}",
                f"  Edge: {self.edge:+.1%} | Confidenza: {self.confidenza}",
                f"{icona} {self.consiglio} — {self.motivo}",
            ]
            if self.stake_consigliato:
                out.append(f"  💰 Stake consigliato: €{self.stake_consigliato:.2f}")
        else:
            out += [f"💶 Quote non fornite → nessun consiglio di scommessa.",
                    f"   {VERIFY_ODDS} e riprova con le quote."]
        out.append(line)
        return "\n".join(out)


def _context_notes(home: str, away: str, venue_country: str | None) -> list[str]:
    """Fattori contestuali VERIFICATI (host, debuttante, campione, tier)."""
    notes: list[str] = []
    if home in HOSTS and venue_country == home:
        notes.append(f"{home} gioca in casa (vantaggio host: +{WORLD_CUP_TRENDS['host_goal_diff_boost']} gol diff. storico)")
    for t in (home, away):
        if t in DEBUTANTS:
            notes.append(f"{t} è debuttante (storicamente perde la 1ª nel {WORLD_CUP_TRENDS['debutant_loses_first_match']:.0%} dei casi)")
        if t == DEFENDING_CHAMPION:
            notes.append(f"{t} è campione in carica (negli ultimi 3 Mondiali il campione è uscito ai gironi nel 75% dei casi)")
    th, ta = TEAM_TIERS.get(home, 3), TEAM_TIERS.get(away, 3)
    if abs(th - ta) >= 2:
        forte, debole = (home, away) if th < ta else (away, home)
        notes.append(f"{forte} nettamente favorita per tier su {debole}")
    return notes


def _news_notes(team: str, items: "list[NewsItem] | None") -> list[str]:
    """Note dalle news: fonte + data + titolo + URL + tag sentiment (max 2)."""
    if items is None:
        return []
    if not items:
        return [f"🗞️ News {team}: non disponibili (offline) — DATO MANCANTE"]
    out: list[str] = []
    for it in items[:2]:
        s = analyze(f"{it.title} {it.summary}")
        tag = "🟢" if s.score > 0 else ("🔴" if s.score < 0 else "⚪")
        data = (it.published[:16] + "…") if len(it.published) > 16 else it.published
        out.append(f"🗞️ {tag} {it.source} ({data}): {it.title} — {it.url}")
        if s.injury_flag:
            out.append(f"   ⚠️ Possibile assenza per {team} — formazione NON CONFERMATA")
    return out


def build_match_report(
    home: str,
    away: str,
    odds: dict[str, float] | None = None,
    venue_country: str | None = "USA",
    bankroll: float | None = None,
    plan_date: date | None = None,
    model: PoissonModel | None = None,
    news_home: "list[NewsItem] | None" = None,
    news_away: "list[NewsItem] | None" = None,
    model_weight: float | None = None,
) -> MatchReport:
    model = model or PoissonModel()
    probs = model.predict_match(home, away, venue_country)
    notes = _context_notes(home, away, venue_country)

    # Note e morale dalle testate giornalistiche (se fornite).
    md = None
    if news_home is not None or news_away is not None:
        notes += _news_notes(home, news_home) + _news_notes(away, news_away)
        md = morale_delta(news_home or [], news_away or [])
        if (news_home or news_away):
            notes.append(
                f"📰 Morale da news: {home} {team_sentiment(news_home or []):+.2f} "
                f"vs {away} {team_sentiment(news_away or []):+.2f} (Δ {md:+.2f})"
            )

    # Pronostico del modello = esito più probabile.
    base = {"1": probs.prob_1, "X": probs.prob_x, "2": probs.prob_2}
    pronostico = max(base, key=base.get)

    report = MatchReport(
        home=home, away=away, venue_country=venue_country,
        lambda_home=probs.lambda_home, lambda_away=probs.lambda_away,
        prob_1=probs.prob_1, prob_x=probs.prob_x, prob_2=probs.prob_2,
        over_2_5=probs.over_2_5, under_2_5=probs.under_2_5,
        pronostico=pronostico, pronostico_prob=base[pronostico],
        notes=notes, news_morale_delta=md,
    )

    if not odds:
        return report  # niente quote → solo pronostico, nessun consiglio

    # Con le quote: calibra verso il mercato. Le probabilità calibrate diventano
    # quelle di riferimento (più affidabili dei prior grezzi). `model_weight`
    # permette di pesare di più il mercato (es. pronostici: 0.30).
    market_fair = remove_margin(odds["1"], odds["X"], odds["2"])
    if model_weight is None:
        cal = calibrate_1x2(base, market_fair)
    else:
        cal = calibrate_1x2(base, market_fair, weight=model_weight)
    report.prob_1, report.prob_x, report.prob_2 = cal["1"], cal["X"], cal["2"]
    # Pronostico = esito PIÙ PROBABILE (calibrato).
    report.pronostico = max(cal, key=cal.get)
    report.pronostico_prob = cal[report.pronostico]

    # Scommessa = esito col MASSIMO EDGE (può differire dal pronostico).
    best = max(("1", "X", "2"), key=lambda k: cal[k] - 1.0 / odds[k])
    edge = cal[best] - 1.0 / odds[best]

    # Le news abbassano la completezza dati se segnalano un'assenza nella squadra
    # su cui scommetteremmo (più incertezza → meno fiducia, possibile declassamento).
    completeness = 0.85
    bet_team_news = news_home if best == "1" else news_away if best == "2" else None
    if bet_team_news and has_injury_news(bet_team_news):
        completeness -= 0.20
        report.notes.append(
            "⚠️ La confidenza è ridotta: news di possibile assenza nella squadra della bet."
        )
    conf = assess_confidence(completeness)
    betable = is_betable(conf, completeness) and edge >= MIN_EDGE_SINGLE

    # Stake consigliato: bankroll/10, con warm-up della data.
    bankroll = bankroll if bankroll is not None else settings.initial_bankroll
    stake = warmup_stake(round(bankroll / 10, 2), plan_date or date.today())

    report.has_odds = True
    report.odds = odds
    report.bet_outcome = best
    report.edge = edge
    report.implied_prob = 1.0 / odds[best]
    report.confidenza = conf.value
    if betable:
        report.consiglio = "SCOMMETTI"
        report.motivo = f"Edge {edge:+.1%} ≥ 5% e dati sufficienti."
        report.stake_consigliato = stake
    else:
        report.consiglio = "NON SCOMMETTERE"
        if edge < MIN_EDGE_SINGLE:
            report.motivo = f"Edge {edge:+.1%} sotto la soglia del 5%: nessun valore."
        else:
            report.motivo = "Dati insufficienti per un consiglio affidabile."
    return report
