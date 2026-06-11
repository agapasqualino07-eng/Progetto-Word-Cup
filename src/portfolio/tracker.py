"""
Portafoglio persistente — SQLite (solo standard library).

Risolve il gap "i piani non vengono salvati". Registra le bet confermate,
le regola col risultato, aggiorna il bankroll e calcola ROI cumulativo.
Regola 7 della specifica: il portafoglio si aggiorna SOLO su conferma.

Usa `:memory:` nei test, un file `data/worldcupedge.sqlite` in produzione.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

from ..models.schemas import Bet, DailyPlan


@dataclass
class PortfolioSummary:
    bankroll: float
    n_bets: int
    n_settled: int
    n_wins: int
    profit: float
    roi: float


class PortfolioTracker:
    def __init__(self, db_path: str = "data/worldcupedge.sqlite",
                 initial_bankroll: float = 100.0):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
        if self._get_bankroll() is None:
            self._set_bankroll(initial_bankroll)

    # --- schema ------------------------------------------------------------
    def _init_db(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS bankroll (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                amount REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_date TEXT, tipo TEXT, legs TEXT,
                quota REAL, stake REAL,
                stato TEXT DEFAULT 'pending',   -- pending | won | lost
                profit REAL DEFAULT 0
            );
            """
        )
        self.conn.commit()

    # --- bankroll ----------------------------------------------------------
    def _get_bankroll(self) -> float | None:
        row = self.conn.execute("SELECT amount FROM bankroll WHERE id = 1").fetchone()
        return row["amount"] if row else None

    def _set_bankroll(self, amount: float) -> None:
        self.conn.execute(
            "INSERT INTO bankroll (id, amount) VALUES (1, ?) "
            "ON CONFLICT(id) DO UPDATE SET amount = excluded.amount",
            (round(amount, 2),),
        )
        self.conn.commit()

    @property
    def bankroll(self) -> float:
        return self._get_bankroll() or 0.0

    # --- registrazione / regolazione --------------------------------------
    def confirm_plan(self, plan: DailyPlan) -> list[int]:
        """Registra come 'pending' tutte le bet del piano. Ritorna gli id."""
        ids: list[int] = []
        for bet in plan.all_bets:
            ids.append(self._insert_bet(plan.plan_date.isoformat(), bet))
        return ids

    def _insert_bet(self, plan_date: str, bet: Bet) -> int:
        legs = json.dumps(
            [{"partita": f"{l.home}-{l.away}", "esito": l.outcome.value,
              "quota": l.odds} for l in bet.legs]
        )
        cur = self.conn.execute(
            "INSERT INTO bets (plan_date, tipo, legs, quota, stake) "
            "VALUES (?,?,?,?,?)",
            (plan_date, bet.bet_type.value, legs, bet.combined_odds, bet.stake),
        )
        self.conn.commit()
        return cur.lastrowid

    def settle(self, bet_id: int, won: bool) -> float:
        """Regola una bet col risultato e aggiorna il bankroll. Ritorna il profitto."""
        row = self.conn.execute(
            "SELECT stake, quota, stato FROM bets WHERE id = ?", (bet_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Bet {bet_id} inesistente")
        if row["stato"] != "pending":
            raise ValueError(f"Bet {bet_id} già regolata ({row['stato']})")

        profit = row["stake"] * (row["quota"] - 1.0) if won else -row["stake"]
        self.conn.execute(
            "UPDATE bets SET stato = ?, profit = ? WHERE id = ?",
            ("won" if won else "lost", round(profit, 2), bet_id),
        )
        self._set_bankroll(self.bankroll + profit)
        self.conn.commit()
        return round(profit, 2)

    # --- riepilogo ---------------------------------------------------------
    def summary(self, initial_bankroll: float = 100.0) -> PortfolioSummary:
        agg = self.conn.execute(
            "SELECT COUNT(*) n, "
            "SUM(stato != 'pending') settled, "
            "SUM(stato = 'won') wins, "
            "COALESCE(SUM(profit), 0) profit, "
            "COALESCE(SUM(CASE WHEN stato != 'pending' THEN stake END), 0) staked "
            "FROM bets"
        ).fetchone()
        staked = agg["staked"] or 0.0
        roi = (agg["profit"] / staked) if staked else 0.0
        return PortfolioSummary(
            bankroll=round(self.bankroll, 2),
            n_bets=agg["n"] or 0,
            n_settled=agg["settled"] or 0,
            n_wins=agg["wins"] or 0,
            profit=round(agg["profit"] or 0.0, 2),
            roi=roi,
        )

    def close(self) -> None:
        self.conn.close()
