"""
Collector quote — The Odds API con fallback mock.

Strategia (come da specifica):
  LIV 1 — SNAI diretto (Playwright)  → roadmap, non qui
  LIV 2 — The Odds API (questo file) → reale se c'è la chiave
  LIV 3 — Dati mock                  → per sviluppo/test senza chiave

Se la chiave non c'è, il collector restituisce dati MOCK chiaramente
etichettati (`source="MOCK"`): mai spacciare quote finte per reali.
Usa solo la standard library (urllib), così il core resta senza dipendenze.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from ..constants import group_of

ODDS_API_BASE = "https://api.the-odds-api.com/v4"
SPORT_KEY = "soccer_fifa_world_cup"


def _default_window_hours() -> float:
    """Finestra temporale di default (ore): solo partite nelle prossime N ore.
    Così il piano del mattino contiene le partite di OGGI, non tutto il calendario.
    Sovrascrivibile con la variabile d'ambiente PLAN_WINDOW_HOURS."""
    try:
        return float(os.environ.get("PLAN_WINDOW_HOURS", 30.0))
    except (TypeError, ValueError):
        return 30.0


DEFAULT_WINDOW_HOURS = _default_window_hours()


@dataclass
class MatchOdds:
    match_id: str
    home: str
    away: str
    odds_1: float          # vittoria casa
    odds_x: float          # pareggio
    odds_2: float          # vittoria trasferta
    source: str            # "the-odds-api:<book>" oppure "MOCK"
    commence_date: date | None = None
    commence_time: datetime | None = None   # orario di inizio (UTC), per il filtro
    group: str | None = None
    matchday: int | None = None

    @property
    def is_mock(self) -> bool:
        return self.source == "MOCK"


def _parse_iso(value: str | None) -> datetime | None:
    """Parsa un timestamp ISO 8601 (es. '2026-06-12T18:00:00Z') in datetime UTC."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def filter_upcoming(
    matches: list["MatchOdds"],
    within_hours: float | None,
    now: datetime | None = None,
) -> list["MatchOdds"]:
    """
    Tiene solo le partite che iniziano da adesso fino a `within_hours` ore dopo.
    Le partite senza orario noto vengono escluse (non sappiamo collocarle: meglio
    ometterle che mostrarle nel giorno sbagliato). `within_hours=None` → nessun filtro.
    """
    if within_hours is None:
        return matches
    now = now or datetime.now(timezone.utc)
    horizon = now + timedelta(hours=within_hours)
    kept = []
    for m in matches:
        ct = m.commence_time
        if ct is None:
            continue
        if ct.tzinfo is None:
            ct = ct.replace(tzinfo=timezone.utc)
        if now <= ct <= horizon:
            kept.append(m)
    return kept


# ---------------------------------------------------------------------------
# Dati MOCK — partite di esempio per sviluppo. NON sono quote reali.
# Le quote sono plausibili ma inventate: servono solo a far girare la pipeline.
# ---------------------------------------------------------------------------
def mock_matchday(plan_date: date | None = None) -> list[MatchOdds]:
    d = plan_date or date(2026, 6, 16)
    # NB: quote inventate. Alcune sono volutamente "generose" sulle favorite
    # (mercato soft) così, dopo la calibrazione, resta del valore da mostrare;
    # altre sono efficienti e verranno scartate (skip). Serve a dimostrare la
    # selettività della pipeline, non sono prezzi reali.
    raw = [
        ("Spagna", "Capo Verde", 1.70, 4.50, 7.50, 1),   # favorita a quota generosa
        ("Brasile", "Haiti", 1.65, 4.80, 8.00, 1),       # favorita a quota generosa
        ("Argentina", "Algeria", 1.62, 4.20, 6.50, 1),   # favorita a quota generosa
        ("Francia", "Senegal", 1.55, 3.90, 6.00, 1),     # leggermente generosa
        ("Austria", "Giordania", 1.45, 4.10, 6.50, 1),   # efficiente → probabile skip
        ("Norvegia", "Iraq", 1.95, 3.40, 3.90, 1),       # efficiente → probabile skip
    ]
    out: list[MatchOdds] = []
    for i, (home, away, o1, ox, o2, md) in enumerate(raw, start=1):
        out.append(
            MatchOdds(
                match_id=f"mock-{i}",
                home=home,
                away=away,
                odds_1=o1,
                odds_x=ox,
                odds_2=o2,
                source="MOCK",
                commence_date=d,
                group=group_of(home),
                matchday=md,
            )
        )
    return out


class OddsCollector:
    """Recupera le quote 1X2. Con chiave → The Odds API; senza → mock."""

    def __init__(self, api_key: str | None = None, regions: str = "eu"):
        self.api_key = api_key or ""
        self.regions = regions

    def get_odds(
        self,
        use_mock: bool | None = None,
        plan_date: date | None = None,
        within_hours: float | None = DEFAULT_WINDOW_HOURS,
    ) -> list[MatchOdds]:
        """
        use_mock=None  → auto (mock se manca la chiave)
        use_mock=True  → forza mock
        use_mock=False → forza API (errore se manca la chiave)

        Sui dati REALI (API) applica il filtro `within_hours`: tiene solo le
        partite in programma nelle prossime ore. I dati MOCK non vengono filtrati
        (sono deterministici, per demo/test). `within_hours=None` → nessun filtro.
        """
        if use_mock is True or (use_mock is None and not self.api_key):
            return mock_matchday(plan_date)
        if not self.api_key:
            raise RuntimeError("ODDS_API_KEY mancante: impossibile usare The Odds API")
        return filter_upcoming(self._fetch_api(), within_hours)

    def _fetch_api(self) -> list[MatchOdds]:
        url = (
            f"{ODDS_API_BASE}/sports/{SPORT_KEY}/odds/"
            f"?apiKey={self.api_key}&regions={self.regions}&markets=h2h"
            f"&oddsFormat=decimal"
        )
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                events = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, ValueError) as exc:
            raise RuntimeError(f"The Odds API non raggiungibile: {exc}") from exc
        return [m for ev in events if (m := self._parse_event(ev)) is not None]

    @staticmethod
    def _parse_event(ev: dict) -> "MatchOdds | None":
        home = ev.get("home_team")
        away = ev.get("away_team")
        bookmakers = ev.get("bookmakers") or []
        if not home or not away or not bookmakers:
            return None
        book = bookmakers[0]
        market = next((m for m in book.get("markets", []) if m.get("key") == "h2h"), None)
        if not market:
            return None
        prices = {o["name"]: o["price"] for o in market.get("outcomes", [])}
        o1, o2 = prices.get(home), prices.get(away)
        ox = prices.get("Draw")
        if not (o1 and ox and o2):
            return None
        ct = _parse_iso(ev.get("commence_time"))
        return MatchOdds(
            match_id=ev.get("id", f"{home}-{away}"),
            home=home,
            away=away,
            odds_1=float(o1),
            odds_x=float(ox),
            odds_2=float(o2),
            source=f"the-odds-api:{book.get('key', '?')}",
            commence_date=ct.date() if ct else None,
            commence_time=ct,
            group=group_of(home),
        )
