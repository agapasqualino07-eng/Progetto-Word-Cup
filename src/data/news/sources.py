"""
Testate giornalistiche (feed RSS) per il news engine.

Ogni fonte è un feed RSS pubblico: si parsano titolo, link, data e sommario.
Gli URL sono "best effort" — vanno verificati; il collector gestisce con
grazia i feed irraggiungibili. Aggiungerne altri = aggiungere righe qui.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NewsSource:
    name: str
    rss_url: str
    lingua: str


# Testate principali per il calcio internazionale (it/en/es/fr/de).
NEWS_SOURCES: list[NewsSource] = [
    NewsSource("BBC Sport", "https://feeds.bbci.co.uk/sport/football/rss.xml", "en"),
    NewsSource("Sky Sport", "https://www.skysports.com/rss/12040", "en"),
    NewsSource("Guardian Football", "https://www.theguardian.com/football/rss", "en"),
    NewsSource("Gazzetta", "https://www.gazzetta.it/rss/calcio.xml", "it"),
    NewsSource("Corriere dello Sport", "https://www.corrieredellosport.it/rss/calcio", "it"),
    NewsSource("Marca", "https://e00-marca.uecdn.es/rss/futbol/mas-futbol.xml", "es"),
    NewsSource("AS", "https://as.com/rss/futbol/portada.xml", "es"),
    NewsSource("L'Équipe", "https://www.lequipe.fr/rss/actu_rss_Football.xml", "fr"),
    NewsSource("Kicker", "https://newsfeed.kicker.de/news/fussball", "de"),
]
