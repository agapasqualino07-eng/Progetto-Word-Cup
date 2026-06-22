"""
Raccoglitore di quote storiche REALI per il backtest ROI/CLV.

Il backtester ha bisogno, per ogni partita: quote di APERTURA, quote di CHIUSURA
e RISULTATO reali. Non sono scaricabili "dal passato" da fonti gratuite — ma il
Mondiale è in corso: questo modulo le raccoglie MENTRE accadono.

Flusso (eseguito periodicamente, es. ogni 8 ore, dal workflow):
  1. snapshot : salva le quote correnti di ogni partita in arrivo (append).
                → la 1ª istantanea per partita = apertura; l'ultima prima del
                  calcio d'inizio = chiusura.
  2. risultati: a partita finita, legge il risultato reale (endpoint /scores).
  3. build    : da snapshot + risultati costruisce data/history.csv (quote
                apertura+chiusura + esito) consumato dal backtester.

Solo standard library (urllib). Nessun dato inventato: senza chiave o senza
partite, semplicemente non scrive nulla.
"""
from __future__ import annotations

import csv
import json
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .odds_api import ODDS_API_BASE, SPORT_KEY, MatchOdds, OddsCollector

# File tracciati nel repo (dati pubblici → persistono tra i run del workflow).
SNAPSHOTS_PATH = "data/odds_snapshots.csv"
HISTORY_OUT_PATH = "data/history.csv"

SNAPSHOT_FIELDS = [
    "captured_at", "match_id", "home", "away", "commence_time",
    "odds_1", "odds_x", "odds_2",
]


def _now_iso(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).isoformat()


def snapshot_rows(matches: list[MatchOdds], now: datetime | None = None) -> list[dict]:
    """Trasforma le quote correnti in righe-istantanea (funzione pura, testabile)."""
    ts = _now_iso(now)
    rows = []
    for m in matches:
        if m.is_mock:
            continue  # mai salvare quote finte nello storico
        rows.append({
            "captured_at": ts,
            "match_id": m.match_id,
            "home": m.home,
            "away": m.away,
            "commence_time": m.commence_time.isoformat() if m.commence_time else "",
            "odds_1": m.odds_1,
            "odds_x": m.odds_x,
            "odds_2": m.odds_2,
        })
    return rows


def append_snapshots(rows: list[dict], path: str | Path = SNAPSHOTS_PATH) -> int:
    """Aggiunge le righe-istantanea al CSV (crea l'intestazione se serve)."""
    if not rows:
        return 0
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    new_file = not p.exists()
    with p.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SNAPSHOT_FIELDS)
        if new_file:
            w.writeheader()
        w.writerows(rows)
    return len(rows)


def load_snapshots(path: str | Path = SNAPSHOTS_PATH) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    return list(csv.DictReader(p.open(encoding="utf-8")))


def take_snapshot(api_key: str, path: str | Path = SNAPSHOTS_PATH,
                  now: datetime | None = None) -> int:
    """Scarica le quote correnti (tutte le partite future) e le salva."""
    if not api_key:
        return 0
    # within_hours=None: vogliamo TUTTE le partite future, per catturare l'apertura.
    matches = OddsCollector(api_key).get_odds(use_mock=False, within_hours=None)
    return append_snapshots(snapshot_rows(matches, now), path)


def fetch_results(api_key: str, days_from: int = 3) -> dict[str, str]:
    """Legge i risultati reali (endpoint /scores) → {match_id: '1'|'X'|'2'}."""
    if not api_key:
        return {}
    url = (f"{ODDS_API_BASE}/sports/{SPORT_KEY}/scores/"
           f"?apiKey={api_key}&daysFrom={days_from}")
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            events = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, ValueError) as exc:
        raise RuntimeError(f"Scores API non raggiungibile: {exc}") from exc
    return results_to_outcomes(events)


def results_to_outcomes(events: list[dict]) -> dict[str, str]:
    """Mappa gli eventi /scores completati in esiti 1/X/2 (funzione pura)."""
    out: dict[str, str] = {}
    for ev in events:
        if not ev.get("completed"):
            continue
        scores = ev.get("scores") or []
        sc = {s.get("name"): s.get("score") for s in scores}
        home, away = ev.get("home_team"), ev.get("away_team")
        try:
            hs, as_ = int(sc[home]), int(sc[away])
        except (KeyError, TypeError, ValueError):
            continue
        mid = ev.get("id", f"{home}-{away}")
        out[mid] = "1" if hs > as_ else ("X" if hs == as_ else "2")
    return out


def build_history(snapshots: list[dict], outcomes: dict[str, str]) -> list[dict]:
    """
    Da snapshot + risultati costruisce le righe per history.csv: per ogni partita
    conclusa, quote di apertura (prima istantanea) e chiusura (ultima prima del
    calcio d'inizio) + esito reale.
    """
    by_match: dict[str, list[dict]] = defaultdict(list)
    for s in snapshots:
        by_match[s["match_id"]].append(s)

    rows = []
    for mid, snaps in by_match.items():
        if mid not in outcomes:
            continue
        snaps.sort(key=lambda s: s["captured_at"])
        opening = snaps[0]
        commence = opening.get("commence_time") or ""
        before = [s for s in snaps if not commence or s["captured_at"] <= commence]
        closing = (before or snaps)[-1]
        # Normalizza i nomi anche qui: gli snapshot più vecchi (pre-fix) sono
        # stati salvati coi nomi inglesi dell'API.
        from .team_names import normalize_team
        rows.append({
            "date": (opening.get("commence_time") or "")[:10],  # YYYY-MM-DD
            "home": normalize_team(opening["home"]),
            "away": normalize_team(opening["away"]),
            "actual": outcomes[mid],
            "open_1": opening["odds_1"], "open_x": opening["odds_x"], "open_2": opening["odds_2"],
            "close_1": closing["odds_1"], "close_x": closing["odds_x"], "close_2": closing["odds_2"],
        })
    return rows


def write_history_csv(rows: list[dict], path: str | Path = HISTORY_OUT_PATH) -> int:
    """Scrive le righe nel formato consumato dal backtester (history_loader)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    cols = ["date", "home", "away", "actual", "open_1", "open_x", "open_2",
            "close_1", "close_x", "close_2"]
    with p.open("w", encoding="utf-8", newline="") as f:
        f.write("# Quote storiche REALI raccolte durante il Mondiale 2026.\n")
        f.write("# Generato da src/data/odds_history.py (snapshot + risultati reali).\n")
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def _main() -> None:
    import sys

    from ..config import settings

    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    key = settings.odds_api_key
    if not key:
        print("⚠️  ODDS_API_KEY assente: niente da raccogliere (mai quote finte).")
        return

    if cmd in ("snapshot", "all"):
        n = take_snapshot(key)
        print(f"📸 Snapshot: {n} quote salvate in {SNAPSHOTS_PATH}.")
    if cmd in ("build", "all"):
        snaps = load_snapshots()
        outcomes = fetch_results(key)
        rows = build_history(snaps, outcomes)
        n = write_history_csv(rows)
        print(f"🧱 Storico: {n} partite concluse → {HISTORY_OUT_PATH} "
              f"(da {len({s['match_id'] for s in snaps})} partite osservate).")


if __name__ == "__main__":
    _main()
