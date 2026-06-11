"""
Sentiment e impatto delle notizie — lessico trasparente (niente ML/black-box).

Un lessico esplicito è verificabile e privo di allucinazioni: si vede esattamente
perché una notizia è negativa (es. contiene "infortunio"). Multilingua di base
(it/en/es/fr). Sostituibile in roadmap con un modello calibrato.
"""
from __future__ import annotations

from dataclasses import dataclass

# Termini che indicano problemi (calo di forza / disponibilità).
NEGATIVE = {
    "infortun", "lesion", "ko", "out", "salta", "stop", "acciacc", "dubbio",
    "squalific", "diffidat", "crisi", "sconfitt", "eliminat", "fuori", "assenza",
    "injur", "doubt", "suspend", "ban", "crisis", "ruled out",
    "blessure", "suspendu", "lesión", "duda", "baja", "sancionado",
}
# Termini positivi (forma / recuperi).
POSITIVE = {
    "recuper", "torna", "in forma", "fiducia", "rinnov", "convocat", "pronto",
    "vittoria", "stella", "trascin",
    "return", "fit", "confidence", "boost", "win",
    "récupér", "titulaire", "recuperad", "victoria",
}
# Sottoinsieme che segnala specificamente un problema di DISPONIBILITÀ.
INJURY_OR_BAN = {
    "infortun", "lesion", "ko", "out", "salta", "stop", "squalific", "diffidat",
    "assenza", "injur", "ruled out", "suspend", "ban", "blessure", "baja", "lesión",
}


@dataclass
class NewsSentiment:
    score: float            # [-1, 1]: <0 negativo, >0 positivo
    injury_flag: bool       # True se segnala possibile assenza
    n_positive: int
    n_negative: int


def _count(text: str, terms: set[str]) -> int:
    t = text.lower()
    return sum(1 for term in terms if term in t)


def analyze(text: str) -> NewsSentiment:
    """Sentiment di un testo (titolo + sommario)."""
    pos = _count(text, POSITIVE)
    neg = _count(text, NEGATIVE)
    total = pos + neg
    score = 0.0 if total == 0 else (pos - neg) / total
    return NewsSentiment(
        score=round(score, 3),
        injury_flag=_count(text, INJURY_OR_BAN) > 0,
        n_positive=pos,
        n_negative=neg,
    )
