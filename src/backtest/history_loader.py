"""
Loader di dati storici REALI per il backtester.

Il backtester è il gate prima del denaro reale, ma vale solo quanto i dati su
cui gira. Finora girava su `sample_data` (righe SINTETICHE, etichettate). Questo
modulo carica partite storiche VERE da un file CSV fornito dall'utente.

Principio anti-allucinazione (vedi CLAUDE.md):
  - NON si inventano mai partite, quote o risultati.
  - File assente  -> errore chiaro / `None` (il chiamante usa il sample etichettato),
    MAI dati finti spacciati per reali.
  - Riga malformata -> errore con numero di riga, non un valore "indovinato".

Formato CSV (intestazione obbligatoria, una partita per riga):
    home,away,actual,open_1,open_x,open_2,close_1,close_x,close_2

  - `actual`        esito reale: "1" (casa) | "X" (pari) | "2" (trasferta)
  - `open_*`        quote 1/X/2 alla scommessa (apertura)
  - `close_*`       quote 1/X/2 alla chiusura (servono per il CLV)
  - righe vuote e righe che iniziano con '#' (commenti) vengono ignorate.

Dove mettere il file reale: `data/raw/history.csv` (cartella già in .gitignore).
Template di esempio committato: `data/history_template.csv`.
"""
from __future__ import annotations

import csv
import os
from pathlib import Path

from .sample_data import HistoricalMatch

# Percorsi cercati in ordine: prima il file privato (non versionato), poi quello
# committato che il raccoglitore quote aggiorna (data/history.csv).
DEFAULT_HISTORY_PATHS = ("data/raw/history.csv", "data/history.csv")
DEFAULT_HISTORY_PATH = DEFAULT_HISTORY_PATHS[0]  # retro-compatibilità
# Variabile d'ambiente per sovrascrivere il percorso.
ENV_HISTORY_PATH = "WCE_HISTORY_CSV"

REQUIRED_COLUMNS = (
    "home", "away", "actual",
    "open_1", "open_x", "open_2",
    "close_1", "close_x", "close_2",
)
_VALID_OUTCOMES = {"1", "X", "2"}


class HistoryLoadError(ValueError):
    """Errore di caricamento/validazione del file storico (messaggio esplicito)."""


def _parse_odds(value: str, *, field: str, line: int) -> float:
    try:
        odds = float(value)
    except (TypeError, ValueError):
        raise HistoryLoadError(
            f"Riga {line}: quota non numerica in '{field}': {value!r}"
        ) from None
    if odds <= 1.0:
        raise HistoryLoadError(
            f"Riga {line}: quota non valida in '{field}': {odds} (dev'essere > 1.0)"
        )
    return odds


def _iter_data_lines(text: str):
    """Restituisce (numero_riga, contenuto) saltando righe vuote e commenti '#'."""
    for i, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        yield i, raw


def parse_history_csv(text: str) -> list[HistoricalMatch]:
    """Valida e converte il testo CSV in una lista di HistoricalMatch."""
    data_lines = list(_iter_data_lines(text))
    if not data_lines:
        raise HistoryLoadError("File storico vuoto: nessuna riga dati (solo commenti/vuote).")

    line_numbers = [ln for ln, _ in data_lines]
    reader = csv.DictReader([content for _, content in data_lines])

    if reader.fieldnames is None:
        raise HistoryLoadError("Intestazione CSV mancante.")
    header = [h.strip() for h in reader.fieldnames]
    missing = [c for c in REQUIRED_COLUMNS if c not in header]
    if missing:
        raise HistoryLoadError(
            "Colonne mancanti nell'intestazione: "
            + ", ".join(missing)
            + f". Attese: {', '.join(REQUIRED_COLUMNS)}."
        )

    matches: list[HistoricalMatch] = []
    # La prima data-line è l'intestazione; le righe dati partono dalla seconda.
    for row, src_line in zip(reader, line_numbers[1:]):
        home = (row.get("home") or "").strip()
        away = (row.get("away") or "").strip()
        actual = (row.get("actual") or "").strip().upper()
        if not home or not away:
            raise HistoryLoadError(f"Riga {src_line}: 'home'/'away' non possono essere vuoti.")
        if actual not in _VALID_OUTCOMES:
            raise HistoryLoadError(
                f"Riga {src_line}: 'actual' = {actual!r} non valido (atteso 1 | X | 2)."
            )
        matches.append(
            HistoricalMatch(
                home=home,
                away=away,
                actual=actual,
                open_1=_parse_odds(row["open_1"], field="open_1", line=src_line),
                open_x=_parse_odds(row["open_x"], field="open_x", line=src_line),
                open_2=_parse_odds(row["open_2"], field="open_2", line=src_line),
                close_1=_parse_odds(row["close_1"], field="close_1", line=src_line),
                close_x=_parse_odds(row["close_x"], field="close_x", line=src_line),
                close_2=_parse_odds(row["close_2"], field="close_2", line=src_line),
                date=(row.get("date") or "").strip(),  # opzionale
            )
        )
    return matches


def load_history_csv(path: str | os.PathLike) -> list[HistoricalMatch]:
    """Carica e valida le partite storiche da un file CSV. Lancia HistoryLoadError."""
    p = Path(path)
    if not p.exists():
        raise HistoryLoadError(
            f"DATO MANCANTE: file storico non trovato: {p}. "
            f"Crea '{DEFAULT_HISTORY_PATH}' (vedi data/history_template.csv)."
        )
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:  # permessi, ecc.
        raise HistoryLoadError(f"Impossibile leggere {p}: {exc}") from exc
    return parse_history_csv(text)


def load_real_history(path: str | os.PathLike | None = None) -> list[HistoricalMatch] | None:
    """
    Tenta di caricare dati storici REALI.

    Ordine del percorso: argomento `path` > variabile d'ambiente WCE_HISTORY_CSV
    > default (data/raw/history.csv, poi data/history.csv). Se nessun file esiste
    restituisce None (il chiamante può ripiegare sul sample ETICHETTATO). Se il
    file esiste ma è malformato lancia HistoryLoadError: meglio fermarsi.
    """
    explicit = path or os.environ.get(ENV_HISTORY_PATH)
    candidates = [explicit] if explicit else list(DEFAULT_HISTORY_PATHS)
    chosen = next((c for c in candidates if c and Path(c).exists()), None)
    if chosen is None:
        return None
    return load_history_csv(chosen)
