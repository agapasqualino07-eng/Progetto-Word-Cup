"""
Dataset DI ESEMPIO per il backtester.

⚠️  ATTENZIONE: queste NON sono partite o quote reali. Sono righe SINTETICHE
costruite solo per testare la MECCANICA del backtester (calcolo ROI/CLV).
Per un backtest vero servono dati storici reali (Mondiale 2022, Euro 2024):
sostituisci questa funzione con un loader da CSV/DB. Vedi ISTRUZIONI.md.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HistoricalMatch:
    home: str
    away: str
    actual: str            # esito reale: "1" | "X" | "2"
    # quote alla scommessa (opening) e alla chiusura (closing) per il CLV
    open_1: float
    open_x: float
    open_2: float
    close_1: float
    close_x: float
    close_2: float
    date: str = ""         # data partita "YYYY-MM-DD" (per schedina/serie storiche)


# Righe sintetiche etichettate. Mix di favorite confermate e sorprese,
# con quote che si muovono sia a favore sia contro (per esercitare il CLV).
_SAMPLE = [
    # home, away, actual, o1, ox, o2, c1, cx, c2
    ("Francia", "Marocco", "1", 1.70, 3.60, 5.00, 1.62, 3.70, 5.40),
    ("Brasile", "Svizzera", "1", 1.55, 3.90, 6.50, 1.50, 4.00, 7.00),
    ("Argentina", "Messico", "1", 1.65, 3.70, 5.20, 1.58, 3.80, 5.60),
    ("Spagna", "Germania", "X", 2.40, 3.30, 2.90, 2.50, 3.25, 2.80),
    ("Inghilterra", "USA", "X", 1.60, 3.80, 6.00, 1.66, 3.70, 5.50),
    ("Portogallo", "Uruguay", "1", 1.85, 3.40, 4.20, 1.80, 3.45, 4.40),
    ("Olanda", "Ecuador", "1", 1.50, 4.00, 7.00, 1.55, 3.90, 6.50),
    ("Croazia", "Belgio", "2", 2.90, 3.20, 2.50, 3.00, 3.20, 2.40),
    ("Giappone", "Spagna", "1", 3.40, 3.50, 2.10, 3.20, 3.50, 2.20),
    ("Senegal", "Olanda", "2", 3.60, 3.40, 2.05, 3.50, 3.40, 2.10),
    ("Marocco", "Portogallo", "1", 3.80, 3.30, 2.00, 3.60, 3.30, 2.05),
    ("Germania", "Costa d'Avorio", "1", 1.45, 4.50, 7.50, 1.42, 4.60, 8.00),
    ("Uruguay", "Corea del Sud", "X", 1.75, 3.50, 4.80, 1.82, 3.45, 4.40),
    ("USA", "Iran", "1", 1.80, 3.50, 4.50, 1.72, 3.55, 4.80),
    ("Belgio", "Canada", "1", 1.40, 4.60, 8.00, 1.45, 4.40, 7.20),
    ("Svizzera", "Camerun", "1", 1.85, 3.40, 4.40, 1.90, 3.35, 4.20),
    ("Brasile", "Serbia", "1", 1.50, 4.10, 6.80, 1.55, 4.00, 6.40),
    ("Francia", "Danimarca", "1", 1.95, 3.50, 3.90, 1.88, 3.55, 4.10),
    ("Argentina", "Polonia", "1", 1.55, 3.90, 6.00, 1.50, 4.00, 6.50),
    ("Inghilterra", "Galles", "1", 1.40, 4.60, 8.50, 1.45, 4.40, 7.80),
    ("Spagna", "Giappone", "2", 1.85, 3.60, 4.20, 2.10, 3.55, 3.50),
    ("Ghana", "Uruguay", "2", 3.50, 3.40, 2.10, 3.30, 3.40, 2.20),
    ("Corea del Sud", "Portogallo", "1", 3.80, 3.50, 1.95, 3.60, 3.50, 2.00),
    ("Australia", "Danimarca", "1", 3.20, 3.10, 2.40, 3.00, 3.10, 2.50),
]


def sample_history() -> list[HistoricalMatch]:
    return [HistoricalMatch(*row) for row in _SAMPLE]
