"""
Anti-allucinazione — il sistema non deve MAI inventare dati.

Regole rigide codificate (knowledge-action gap): la fiducia su una previsione
dipende da quanti dati reali la sostengono e da quanto i modelli concordano.
Sotto soglia → la previsione è SCARTATA dal piano, non "indovinata".
"""
from __future__ import annotations

from enum import Enum

# Regole di verità: vincolano come il sistema comunica, non solo cosa calcola.
TRUTH_RULES: tuple[str, ...] = (
    "MAI inventare statistiche → 'DATO MANCANTE'",
    "MAI inventare quote → 'VERIFICA SU SNAI'",
    "MAI inventare formazioni → 'NON CONFERMATA'",
    "MAI dire 'sicuro' → ALTA/MEDIA/BASSA/INSUFFICIENTE",
    "MAI inventare news → fonte + data + URL",
    "Completezza dati < 60% → SKIP",
    "Se Poisson e ML discordano > 10% → segnalare",
)

# Placeholder testuali da usare quando un dato manca (mai un numero finto).
MISSING_DATA = "DATO MANCANTE"
VERIFY_ODDS = "VERIFICA SU SNAI"
LINEUP_UNCONFIRMED = "NON CONFERMATA"


class ConfidenceLevel(str, Enum):
    """Livelli di fiducia. Non esiste 'sicuro'."""
    ALTA = "ALTA"            # >=90% dati, modelli allineati
    MEDIA = "MEDIA"          # 70-89% dati
    BASSA = "BASSA"          # 50-69% dati
    INSUFFICIENTE = "INSUFFICIENTE"  # <50% dati → SKIP


# Soglie minime di completezza dati per ciascun livello.
DATA_COMPLETENESS_THRESHOLDS: dict[ConfidenceLevel, float] = {
    ConfidenceLevel.ALTA: 0.90,
    ConfidenceLevel.MEDIA: 0.70,
    ConfidenceLevel.BASSA: 0.50,
}

# Scarto massimo tollerato tra Poisson e ensemble ML prima di declassare.
MODEL_DISAGREEMENT_LIMIT = 0.10
# Sotto questa completezza la previsione è esclusa dal piano.
MIN_DATA_COMPLETENESS = 0.60


def assess_confidence(
    data_completeness: float,
    model_disagreement: float = 0.0,
) -> ConfidenceLevel:
    """
    Determina il livello di fiducia da:
      - data_completeness: frazione [0,1] di feature realmente disponibili;
      - model_disagreement: |prob_poisson - prob_ml| sull'esito scelto.

    Se i modelli discordano oltre la soglia, la fiducia viene declassata di
    un livello (un disaccordo forte è un segnale di incertezza reale).
    """
    if data_completeness < DATA_COMPLETENESS_THRESHOLDS[ConfidenceLevel.BASSA]:
        return ConfidenceLevel.INSUFFICIENTE

    if data_completeness >= DATA_COMPLETENESS_THRESHOLDS[ConfidenceLevel.ALTA]:
        level = ConfidenceLevel.ALTA
    elif data_completeness >= DATA_COMPLETENESS_THRESHOLDS[ConfidenceLevel.MEDIA]:
        level = ConfidenceLevel.MEDIA
    else:
        level = ConfidenceLevel.BASSA

    if model_disagreement > MODEL_DISAGREEMENT_LIMIT:
        level = _downgrade(level)
    return level


def is_betable(level: ConfidenceLevel, data_completeness: float) -> bool:
    """Una selezione entra nel piano solo se supera la soglia minima."""
    return (
        level is not ConfidenceLevel.INSUFFICIENTE
        and data_completeness >= MIN_DATA_COMPLETENESS
    )


def confidence_score(level: ConfidenceLevel) -> float:
    """Punteggio numerico [0,1] usato per ordinare le selezioni."""
    return {
        ConfidenceLevel.ALTA: 1.0,
        ConfidenceLevel.MEDIA: 0.75,
        ConfidenceLevel.BASSA: 0.5,
        ConfidenceLevel.INSUFFICIENTE: 0.0,
    }[level]


_ORDER = [
    ConfidenceLevel.ALTA,
    ConfidenceLevel.MEDIA,
    ConfidenceLevel.BASSA,
    ConfidenceLevel.INSUFFICIENTE,
]


def _downgrade(level: ConfidenceLevel) -> ConfidenceLevel:
    i = _ORDER.index(level)
    return _ORDER[min(i + 1, len(_ORDER) - 1)]
