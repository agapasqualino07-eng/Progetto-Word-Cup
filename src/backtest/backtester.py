"""
Backtester walk-forward — il GATE obbligatorio prima del denaro reale.

Per ogni partita storica:
  1. il modello stima 1/X/2;
  2. si sceglie l'esito con edge massimo alle quote di apertura;
  3. se edge >= soglia → si piazza una bet flat;
  4. si regola l'esito col risultato reale e si calcola il P&L;
  5. si misura il CLV (Closing Line Value): abbiamo battuto la chiusura?

REGOLA: si va live solo se ROI > 0 E CLV medio > 0. Il CLV è il predittore
più affidabile di edge reale: vincere contro la linea di chiusura conta più
del singolo risultato.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..betting.value_engine import MIN_EDGE_SINGLE, remove_margin
from ..ml.calibration import calibrate_1x2
from ..ml.poisson_model import PoissonModel
from .sample_data import HistoricalMatch, sample_history


@dataclass
class BacktestResult:
    n_matches: int
    n_bets: int
    n_wins: int
    total_staked: float
    profit: float
    roi: float
    avg_clv: float
    hit_rate: float

    def passed(self) -> bool:
        """Gate: ROI e CLV medio entrambi positivi."""
        return self.roi > 0 and self.avg_clv > 0

    def summary(self) -> str:
        esito = "✅ PASS — si può valutare il live" if self.passed() else "❌ FAIL — NON andare live"
        return (
            f"Backtest su {self.n_matches} partite | bet piazzate: {self.n_bets}\n"
            f"  Win rate : {self.hit_rate:.1%} ({self.n_wins}/{self.n_bets})\n"
            f"  Puntato  : €{self.total_staked:.2f}\n"
            f"  Profitto : €{self.profit:+.2f}\n"
            f"  ROI      : {self.roi:+.1%}\n"
            f"  CLV medio: {self.avg_clv:+.2%}\n"
            f"  {esito}"
        )


class Backtester:
    def __init__(
        self,
        model: PoissonModel | None = None,
        stake: float = 10.0,
        min_edge: float = MIN_EDGE_SINGLE,
    ):
        self.model = model or PoissonModel()
        self.stake = stake
        self.min_edge = min_edge

    def run(self, history: list[HistoricalMatch] | None = None) -> BacktestResult:
        history = history if history is not None else sample_history()

        n_bets = n_wins = 0
        total_staked = profit = 0.0
        clv_sum = 0.0

        for m in history:
            probs = self.model.predict_match(m.home, m.away, venue_country=None)
            # Calibrazione verso il mercato (come nella pipeline live).
            market_fair = remove_margin(m.open_1, m.open_x, m.open_2)
            cal = calibrate_1x2(
                {"1": probs.prob_1, "X": probs.prob_x, "2": probs.prob_2},
                market_fair,
            )
            # Mappa esito → (prob calibrata, quota apertura, quota chiusura).
            options = {
                "1": (cal["1"], m.open_1, m.close_1),
                "X": (cal["X"], m.open_x, m.close_x),
                "2": (cal["2"], m.open_2, m.close_2),
            }
            # Scegli l'esito con edge massimo all'apertura.
            outcome = max(
                options, key=lambda k: options[k][0] - 1.0 / options[k][1]
            )
            model_prob, open_odds, close_odds = options[outcome]
            edge = model_prob - 1.0 / open_odds
            if edge < self.min_edge:
                continue  # SKIP: nessun valore

            n_bets += 1
            total_staked += self.stake
            # CLV: quanto la nostra quota batte la chiusura (positivo = bene).
            clv_sum += (open_odds / close_odds) - 1.0

            if outcome == m.actual:
                n_wins += 1
                profit += self.stake * (open_odds - 1.0)
            else:
                profit -= self.stake

        roi = profit / total_staked if total_staked else 0.0
        avg_clv = clv_sum / n_bets if n_bets else 0.0
        hit_rate = n_wins / n_bets if n_bets else 0.0
        return BacktestResult(
            n_matches=len(history),
            n_bets=n_bets,
            n_wins=n_wins,
            total_staked=round(total_staked, 2),
            profit=round(profit, 2),
            roi=roi,
            avg_clv=avg_clv,
            hit_rate=hit_rate,
        )


if __name__ == "__main__":
    print(Backtester().run().summary())
