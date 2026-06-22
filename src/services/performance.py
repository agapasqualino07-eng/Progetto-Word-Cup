"""
Scoreboard delle prestazioni su partite REALI già giocate.

Risponde alla domanda 'sto vincendo o perdendo?' con dati veri, confrontando
più strategie sulle stesse partite concluse (data/history.csv, alimentato dal
raccoglitore). Si aggiorna da solo man mano che il dataset cresce.

Strategie misurate (stake €10):
  - PRONOSTICI   : quante volte l'esito previsto (1/X/2) è uscito davvero.
  - FLAT @apertura: €10 sull'esito previsto, a quota di apertura.
  - FLAT @chiusura: idem, a quota di chiusura (più realistico vicino al via).
  - VALUE bet    : solo dove edge ≥ 5% (la strategia prudente del piano) + CLV.

Onestà: nessun dato inventato; con poche partite i numeri sono RUMORE e il
report lo dichiara apertamente.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..backtest.backtester import Backtester
from ..backtest.history_loader import load_real_history
from ..backtest.sample_data import HistoricalMatch
from ..ml.poisson_model import PoissonModel
from ..services.forecast import FORECAST_MODEL_WEIGHT
from ..services.match_report import build_match_report

STAKE = 10.0
# Sotto questo numero di partite, i risultati sono troppo pochi per concludere.
MIN_MEANINGFUL = 25


@dataclass
class StrategyResult:
    name: str
    n_bets: int
    n_wins: int
    profit: float

    @property
    def roi(self) -> float:
        staked = self.n_bets * STAKE
        return self.profit / staked if staked else 0.0


@dataclass
class Performance:
    n_matches: int
    pronostici_correct: int
    flat_open: StrategyResult
    flat_close: StrategyResult
    value: StrategyResult
    avg_clv: float
    schedina: SchedinaRecord
    calibration: list[tuple[str, int, float, float]]

    @property
    def hit_rate(self) -> float:
        return self.pronostici_correct / self.n_matches if self.n_matches else 0.0

    @property
    def meaningful(self) -> bool:
        return self.n_matches >= MIN_MEANINGFUL


@dataclass
class MatchPred:
    date: str
    pronostico: str
    prob: float
    win: bool
    open_odds: float   # quota dell'esito previsto all'apertura
    close_odds: float


def _predict_all(model: PoissonModel, history: list[HistoricalMatch]) -> list[MatchPred]:
    """Pronostico (peso mercato) + esito reale per ogni partita, una volta sola."""
    out = []
    for m in history:
        o_open = {"1": m.open_1, "X": m.open_x, "2": m.open_2}
        rep = build_match_report(m.home, m.away, odds=o_open, venue_country=None,
                                 model=model, model_weight=FORECAST_MODEL_WEIGHT)
        pick = rep.pronostico
        out.append(MatchPred(
            date=m.date, pronostico=pick, prob=rep.pronostico_prob,
            win=(pick == m.actual),
            open_odds={"1": m.open_1, "X": m.open_x, "2": m.open_2}[pick],
            close_odds={"1": m.close_1, "X": m.close_x, "2": m.close_2}[pick],
        ))
    return out


@dataclass
class SchedinaRecord:
    n_days: int
    won: int
    profit: float        # P&L virtuale €10/giorno

    @property
    def roi(self) -> float:
        staked = self.n_days * STAKE
        return self.profit / staked if staked else 0.0


def schedina_record(preds: list[MatchPred], size: int = 3) -> SchedinaRecord:
    """Schedina giornaliera = i `size` esiti più probabili del giorno (€10/giorno).
    Vince solo se TUTTE le gambe azzeccano. Richiede la data delle partite."""
    by_day: dict[str, list[MatchPred]] = {}
    for p in preds:
        if p.date:
            by_day.setdefault(p.date, []).append(p)
    won = 0
    profit = 0.0
    days = 0
    for day, ps in by_day.items():
        if len(ps) < 2:
            continue  # una multipla ha senso da 2 gambe in su
        days += 1
        legs = sorted(ps, key=lambda x: x.prob, reverse=True)[:size]
        if all(l.win for l in legs):
            won += 1
            quota = 1.0
            for l in legs:
                quota *= l.open_odds
            profit += STAKE * (quota - 1.0)
        else:
            profit -= STAKE
    return SchedinaRecord(n_days=days, won=won, profit=round(profit, 2))


def calibration_table(preds: list[MatchPred]) -> list[tuple[str, int, float, float]]:
    """Affidabilità: per fascia di probabilità prevista, (etichetta, n, prob media, hit reale)."""
    bands = [(0.0, 0.45), (0.45, 0.55), (0.55, 0.70), (0.70, 1.01)]
    out = []
    for lo, hi in bands:
        grp = [p for p in preds if lo <= p.prob < hi]
        if not grp:
            continue
        avg_p = sum(p.prob for p in grp) / len(grp)
        hit = sum(p.win for p in grp) / len(grp)
        out.append((f"{int(lo*100)}-{int(hi*100)}%", len(grp), avg_p, hit))
    return out


def evaluate_performance(
    history: list[HistoricalMatch],
    model: PoissonModel | None = None,
) -> Performance:
    model = model or PoissonModel()
    preds = _predict_all(model, history)
    correct = sum(p.win for p in preds)
    p_open = sum(STAKE * (p.open_odds - 1) if p.win else -STAKE for p in preds)
    p_close = sum(STAKE * (p.close_odds - 1) if p.win else -STAKE for p in preds)

    # Strategia VALUE: la usa il backtester (edge ≥ 5%, quota apertura, + CLV).
    bt = Backtester(model=model, stake=STAKE).run(history)

    n = len(history)
    return Performance(
        n_matches=n,
        pronostici_correct=correct,
        flat_open=StrategyResult("Flat €10 @apertura", n, correct, round(p_open, 2)),
        flat_close=StrategyResult("Flat €10 @chiusura", n, correct, round(p_close, 2)),
        value=StrategyResult("Value bet (edge≥5%)", bt.n_bets, bt.n_wins, bt.profit),
        avg_clv=bt.avg_clv,
        schedina=schedina_record(preds),
        calibration=calibration_table(preds),
    )


def _fmt(s: StrategyResult) -> str:
    return f"  {s.name}: €{s.profit:+.2f} (ROI {s.roi:+.1%}, {s.n_wins}/{s.n_bets})"


def format_performance_report(perf: Performance) -> str:
    line = "━" * 28
    out = [
        line,
        "📈 COME STA ANDANDO (partite reali giocate)",
        "",
        f"Partite valutate: {perf.n_matches}",
        f"🎯 Pronostici azzeccati: {perf.pronostici_correct}/{perf.n_matches} "
        f"({perf.hit_rate:.0%})",
        "",
        "💶 Se avessi puntato €10:",
        _fmt(perf.flat_open),
        _fmt(perf.flat_close),
        _fmt(perf.value) + f"  · CLV {perf.avg_clv:+.1%}",
    ]

    sc = perf.schedina
    if sc.n_days:
        out += ["",
                f"🎫 Schedina giornaliera (top-3): vinte {sc.won}/{sc.n_days} "
                f"· P&L €{sc.profit:+.2f} (ROI {sc.roi:+.1%})"]

    if perf.calibration:
        out += ["", "🎚️ Affidabilità (previsto → reale):"]
        for label, k, avg_p, hit in perf.calibration:
            spia = "✅" if abs(avg_p - hit) <= 0.10 else "⚠️"
            out.append(f"  {spia} fascia {label}: dice {avg_p:.0%}, esce {hit:.0%} (n={k})")
    if not perf.meaningful:
        out += ["",
                f"⚠️ Solo {perf.n_matches} partite: campione PICCOLO, numeri ancora "
                f"rumore. Servono ≥{MIN_MEANINGFUL} partite per fidarsi. Il dato "
                "cresce da solo ogni giorno."]
    else:
        out += ["", "ℹ️ Live solo con ROI e CLV positivi e stabili. Gioca responsabile."]
    out.append(line)
    return "\n".join(out)


def build_report(model: PoissonModel | None = None) -> str | None:
    """Carica lo storico reale e produce il report. None se non c'è ancora nulla."""
    history = load_real_history()
    if not history:
        return None
    return format_performance_report(evaluate_performance(history, model))


if __name__ == "__main__":
    from ..services.model_provider import get_default_model

    model, _ = get_default_model()
    report = build_report(model)
    print(report or "Nessuna partita conclusa ancora: niente report.")
