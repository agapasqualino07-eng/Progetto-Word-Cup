"""
Pronostici di giornata — il risultato previsto per OGNI partita in finestra.

A differenza del piano scommesse (che seleziona solo le partite con valore),
qui diamo SEMPRE un pronostico per ogni partita: esito più probabile (1/X/2),
probabilità, risultato esatto più probabile e livello di fiducia.

Onestà (anti-allucinazione): è una STIMA del modello (Poisson + rating FIFA
reali, calibrato sul mercato quando ci sono le quote). Mai "sicuro": solo
ALTA/MEDIA/BASSA. Se in futuro ci saranno news reali, `build_match_report` le
integra già; qui restano opzionali e non si inventa nulla.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..anti_hallucination import ConfidenceLevel
from ..constants import HOSTS
from ..data.odds_api import MatchOdds
from ..ml.poisson_model import MAX_GOALS, PoissonModel, poisson_pmf
from .match_report import build_match_report

_OUTCOME_LABEL = {"1": "vittoria casa", "X": "pareggio", "2": "vittoria trasferta"}
_CONF_EMOJI = {
    ConfidenceLevel.ALTA: "🟢",
    ConfidenceLevel.MEDIA: "🟡",
    ConfidenceLevel.BASSA: "🟠",
    ConfidenceLevel.INSUFFICIENTE: "⚪",
}

# Peso del MODELLO nel blend per i PRONOSTICI (il resto è mercato de-vigato).
# Più basso del 0.5 usato per il value betting, di proposito: per AZZECCARE
# l'esito la stima più accurata è la quota (dottrina CLV del progetto); per
# TROVARE VALORE serve invece l'indipendenza del modello. Due scopi, due pesi.
FORECAST_MODEL_WEIGHT = 0.30


@dataclass
class Forecast:
    home: str
    away: str
    outcome: str            # "1" | "X" | "2"
    prob: float             # probabilità dell'esito previsto
    score_home: int         # risultato esatto più probabile (coerente con outcome)
    score_away: int
    confidence: ConfidenceLevel
    odds: float | None = None   # quota dell'esito previsto (se disponibile)


def _confidence_from_prob(prob: float) -> ConfidenceLevel:
    """Fiducia dal margine del pronostico (mai 'sicuro')."""
    if prob >= 0.55:
        return ConfidenceLevel.ALTA
    if prob >= 0.42:
        return ConfidenceLevel.MEDIA
    return ConfidenceLevel.BASSA


def most_likely_score(lambda_home: float, lambda_away: float, outcome: str) -> tuple[int, int]:
    """Risultato esatto più probabile COERENTE con l'esito previsto (1/X/2)."""
    hp = [poisson_pmf(i, lambda_home) for i in range(MAX_GOALS + 1)]
    ap = [poisson_pmf(j, lambda_away) for j in range(MAX_GOALS + 1)]
    best = (1, 0) if outcome == "1" else (0, 1) if outcome == "2" else (1, 1)
    best_p = -1.0
    for i, ph in enumerate(hp):
        for j, pa in enumerate(ap):
            rel = "1" if i > j else ("X" if i == j else "2")
            if rel != outcome:
                continue
            if ph * pa > best_p:
                best_p, best = ph * pa, (i, j)
    return best


def _venue_for(home: str) -> str | None:
    """Al Mondiale solo le nazioni ospitanti giocano 'in casa' (vantaggio ridotto)."""
    return home if home in HOSTS else None


def build_forecasts(
    matches: list[MatchOdds],
    model: PoissonModel | None = None,
) -> list[Forecast]:
    """Un pronostico per ogni partita (ordinate per orario di inizio)."""
    model = model or PoissonModel()
    ordered = sorted(
        matches,
        key=lambda m: (m.commence_time is None, m.commence_time),
    )
    out: list[Forecast] = []
    for m in ordered:
        odds = None if m.is_mock else {"1": m.odds_1, "X": m.odds_x, "2": m.odds_2}
        rep = build_match_report(
            m.home, m.away, odds=odds, venue_country=_venue_for(m.home), model=model,
            model_weight=FORECAST_MODEL_WEIGHT,
        )
        sh, sa = most_likely_score(rep.lambda_home, rep.lambda_away, rep.pronostico)
        all_odds = {"1": m.odds_1, "X": m.odds_x, "2": m.odds_2}
        out.append(Forecast(
            home=m.home, away=m.away,
            outcome=rep.pronostico, prob=rep.pronostico_prob,
            score_home=sh, score_away=sa,
            confidence=_confidence_from_prob(rep.pronostico_prob),
            odds=all_odds.get(rep.pronostico),
        ))
    return out


def build_schedina(forecasts: list[Forecast], size: int = 3) -> list[Forecast]:
    """
    La multipla con la MASSIMA probabilità di vincere: matematicamente è la
    combinazione degli esiti più probabili (P(tutte) = prodotto delle prob).
    Diversa dalle combo del piano scommesse (che massimizzano l'EDGE, non la
    probabilità di vincita). Una gamba per partita, le `size` più probabili.
    """
    ranked = sorted(forecasts, key=lambda f: f.prob, reverse=True)
    return ranked[:size]


def schedina_stats(legs: list[Forecast]) -> tuple[float, float | None]:
    """(probabilità combinata, quota combinata se tutte le quote sono note)."""
    joint = 1.0
    quota: float | None = 1.0
    for leg in legs:
        joint *= leg.prob
        quota = quota * leg.odds if (quota is not None and leg.odds) else None
    return joint, (round(quota, 2) if quota else None)


def _leg_label(f: Forecast) -> str:
    squadra = f.home if f.outcome == "1" else f.away if f.outcome == "2" else "pareggio"
    return f"{f.outcome} ({squadra})" if f.outcome != "X" else "X (pareggio)"


def format_forecasts(forecasts: list[Forecast], stake_demo: float = 10.0) -> str:
    """Sezione 'Pronostici' per il messaggio del mattino (+ schedina più probabile)."""
    if not forecasts:
        return ""
    lines = ["📊 PRONOSTICI DI OGGI (prossime 30h)"]
    for f in forecasts:
        lines.append(
            f"  {_CONF_EMOJI[f.confidence]} {f.home} - {f.away}: {_leg_label(f)} {f.prob:.0%} "
            f"· ipotesi {f.score_home}-{f.score_away} · {f.confidence.value}"
        )

    # Schedina a massima probabilità di vincita (se ci sono almeno 2 partite).
    if len(forecasts) >= 2:
        legs = build_schedina(forecasts, size=min(3, len(forecasts)))
        joint, quota = schedina_stats(legs)
        lines.append("")
        lines.append(f"🎫 SCHEDINA PIÙ PROBABILE ({len(legs)} esiti)")
        def _leg_short(l: Forecast) -> str:
            if l.outcome == "1":
                return f"{l.home} (1)"
            if l.outcome == "2":
                return f"{l.away} (2)"
            return f"{l.home}-{l.away} (X)"
        lines.append("  " + " + ".join(_leg_short(l) for l in legs))
        riga = f"  Prob. di vincerla: {joint:.0%}"
        if quota:
            riga += f" · quota ~{quota} → €{stake_demo:.0f} ➜ €{stake_demo*quota:.2f} potenziali"
        lines.append(riga)
        lines.append("  ℹ️ Massimizza la probabilità di vincita, non il valore atteso.")

    lines.append("ℹ️ Stima del modello (rating FIFA + mercato), non una certezza.")
    return "\n".join(lines)
