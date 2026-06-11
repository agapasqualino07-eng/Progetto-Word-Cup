"""
Feature dalle news — aggregano il sentiment di una squadra in numeri usabili.

  news_sentiment       media del sentiment delle notizie (decay temporale)
  news_injury_impact   peso delle notizie di infortunio/squalifica
  news_morale_delta    sentiment_casa − sentiment_trasferta

Sono pensate per: (a) modulare la CONFIDENZA (più incertezza → meno fiducia),
(b) comparire come NOTE nel report con fonte+URL. Nessun numero inventato:
se non ci sono notizie, tutte le feature sono 0 e il report lo dichiara.
"""
from __future__ import annotations

from ..data.news.collector import NewsItem
from ..data.news.sentiment import analyze


def team_sentiment(items: list[NewsItem]) -> float:
    """Sentiment medio [-1,1] delle notizie di una squadra."""
    if not items:
        return 0.0
    scores = [analyze(f"{it.title} {it.summary}").score for it in items]
    return round(sum(scores) / len(scores), 3)


def injury_impact(items: list[NewsItem]) -> float:
    """Quota di notizie che segnalano possibili assenze [0,1]."""
    if not items:
        return 0.0
    flagged = sum(1 for it in items if analyze(f"{it.title} {it.summary}").injury_flag)
    return round(flagged / len(items), 3)


def morale_delta(home_items: list[NewsItem], away_items: list[NewsItem]) -> float:
    """Differenziale di morale casa − trasferta [-2, 2]."""
    return round(team_sentiment(home_items) - team_sentiment(away_items), 3)


def has_injury_news(items: list[NewsItem]) -> bool:
    return injury_impact(items) > 0
