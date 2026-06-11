"""
News collector — legge i feed RSS delle testate (solo standard library).

Filtra le notizie che citano una nazionale e restituisce NewsItem con
fonte + data + URL (regola anti-allucinazione). Se i feed non sono
raggiungibili (offline / host non in allowlist) → lista VUOTA: il sistema
dirà "news non disponibili", MAI notizie inventate.

`mock_news()` esiste SOLO per demo/test ed è etichettato come tale: non va
usato come se fossero notizie reali.
"""
from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from xml.etree import ElementTree as ET

from .sources import NEWS_SOURCES


@dataclass
class NewsItem:
    source: str
    title: str
    url: str
    published: str          # data come stringa (dal feed); "" se assente
    summary: str = ""

    @property
    def is_mock(self) -> bool:
        return self.source.startswith("MOCK")


def _parse_rss(xml_bytes: bytes, source_name: str) -> list[NewsItem]:
    """Estrae gli <item> da un feed RSS 2.0."""
    items: list[NewsItem] = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return items
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        pub = (it.findtext("pubDate") or "").strip()
        desc = (it.findtext("description") or "").strip()
        if title and link:
            items.append(NewsItem(source_name, title, link, pub, desc))
    return items


def fetch_feed(url: str, source_name: str, timeout: int = 10) -> list[NewsItem]:
    """Scarica e parsa un singolo feed. Lista vuota in caso di errore."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "WorldCupEdge/0.3"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _parse_rss(resp.read(), source_name)
    except (urllib.error.URLError, ValueError, OSError):
        return []


def _mentions(item: NewsItem, team: str) -> bool:
    needle = team.lower()
    return needle in item.title.lower() or needle in item.summary.lower()


class NewsCollector:
    def __init__(self, sources=None):
        self.sources = sources or NEWS_SOURCES

    def for_team(self, team: str, max_items: int = 3,
                 use_mock: bool = False) -> list[NewsItem]:
        """Notizie che citano `team`. Offline → []; use_mock=True → dati demo."""
        if use_mock:
            return mock_news(team)[:max_items]
        found: list[NewsItem] = []
        for src in self.sources:
            for item in fetch_feed(src.rss_url, src.name):
                if _mentions(item, team):
                    found.append(item)
        return found[:max_items]


def mock_news(team: str) -> list[NewsItem]:
    """⚠️ NOTIZIE FINTE, solo per demo/test. Etichettate `MOCK`."""
    oggi = date.today().isoformat()
    return [
        NewsItem("MOCK/Gazzetta", f"{team}, allarme infortunio per un titolare",
                 "https://example.com/mock1", oggi,
                 f"Il CT del {team} valuta le condizioni di un big: possibile forfait."),
        NewsItem("MOCK/Marca", f"{team} carico in vista del match",
                 "https://example.com/mock2", oggi,
                 f"Buone notizie dal ritiro del {team}: recuperato un titolare."),
    ]
