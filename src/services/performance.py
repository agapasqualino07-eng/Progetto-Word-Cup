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

    @property
    def hit_rate(self) -> float:
        return self.pronostici_correct / self.n_matches if self.n_matches else 0.0

    @property
    def meaningful(self) -> bool:
        return self.n_matches >= MIN_MEANINGFUL


def _pronostico(model: PoissonModel, m: HistoricalMatch) -> str:
    """Esito previsto (1/X/2) col peso mercato dei pronostici."""
    odds = {"1": m.open_1, "X": m.open_x, "2": m.open_2}
    rep = build_match_report(m.home, m.away, odds=odds, venue_country=None,
                             model=model, model_weight=FORECAST_MODEL_WEIGHT)
    return rep.pronostico


def evaluate_performance(
    history: list[HistoricalMatch],
    model: PoissonModel | None = None,
) -> Performance:
    model = model or PoissonModel()
    correct = 0
    p_open = p_close = 0.0
    wins_open = wins_close = 0
    for m in history:
        pick = _pronostico(model, m)
        win = pick == m.actual
        correct += win
        o_open = {"1": m.open_1, "X": m.open_x, "2": m.open_2}[pick]
        o_close = {"1": m.close_1, "X": m.close_x, "2": m.close_2}[pick]
        p_open += STAKE * (o_open - 1) if win else -STAKE
        p_close += STAKE * (o_close - 1) if win else -STAKE
        wins_open += win
        wins_close += win

    # Strategia VALUE: la usa il backtester (edge ≥ 5%, quota apertura, + CLV).
    bt = Backtester(model=model, stake=STAKE).run(history)

    n = len(history)
    return Performance(
        n_matches=n,
        pronostici_correct=correct,
        flat_open=StrategyResult("Flat €10 @apertura", n, wins_open, round(p_open, 2)),
        flat_close=StrategyResult("Flat €10 @chiusura", n, wins_close, round(p_close, 2)),
        value=StrategyResult("Value bet (edge≥5%)", bt.n_bets, bt.n_wins, bt.profit),
        avg_clv=bt.avg_clv,
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
