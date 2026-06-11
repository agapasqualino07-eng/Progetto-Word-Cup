"""
Correlazione tra selezioni — evita schedine con gambe dipendenti.

Due esiti correlati non sono indipendenti: moltiplicare le loro quote
sovrastima il valore della schedina. La regola assoluta è non combinare mai
due match dello stesso girone alla 3ª giornata (si giocano in contemporanea).
"""
from __future__ import annotations

from ..constants import CORRELATION
from ..models.schemas import Phase, Selection

# Soglie massime di correlazione ammesse per costruire combo.
MAX_CORRELATION_DOPPIA = 0.30
MAX_CORRELATION_TRIPLA = 0.20


def correlation(a: Selection, b: Selection) -> float:
    """Stima la correlazione [0,1] tra due selezioni."""
    if a.match_id == b.match_id:
        return 1.0  # stesso match: non combinabile

    same_group = a.group is not None and a.group == b.group
    same_day = (
        a.kickoff_date is not None
        and b.kickoff_date is not None
        and a.kickoff_date == b.kickoff_date
    )

    if same_group:
        if a.matchday == 3 and b.matchday == 3:
            return CORRELATION["same_group_matchday_3"]
        if same_day:
            return CORRELATION["same_group_same_day"]
        return CORRELATION["same_group_diff_day"]

    # Stessa confederazione: lieve correlazione (stili, condizioni comuni).
    confeds_a = {a.confederation_home, a.confederation_away} - {None}
    confeds_b = {b.confederation_home, b.confederation_away} - {None}
    if confeds_a & confeds_b:
        return CORRELATION["same_confederation"]

    return CORRELATION["independent"]


def can_combine(selections: list[Selection], max_corr: float) -> bool:
    """True se OGNI coppia di selezioni resta sotto la soglia di correlazione."""
    n = len(selections)
    for i in range(n):
        for j in range(i + 1, n):
            if correlation(selections[i], selections[j]) >= max_corr:
                return False
    return True


def is_forbidden_pair(a: Selection, b: Selection) -> bool:
    """Combinazione vietata in assoluto (stesso girone, 3ª giornata)."""
    return (
        a.group is not None
        and a.group == b.group
        and a.matchday == 3
        and b.matchday == 3
        and a.phase is Phase.GROUP
        and b.phase is Phase.GROUP
    )
