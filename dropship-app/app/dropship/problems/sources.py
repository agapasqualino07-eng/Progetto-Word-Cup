"""Fonti di discussione: interfaccia, adapter MOCK e adapter reali (solo fonti ammesse).

Regole (vedi docs/06-fonti-problemi.md):
- solo API ufficiali o feed RSS/Atom pubblicati dal sito; niente scraping HTML;
- User-Agent identificabile con contatto; rate limit rispettato lato client;
- nessun dato personale: gli adapter NON leggono autore/username/avatar; il
  testo viene ripulito (email, @utente, telefoni, link) e troncato;
- fonti vietate (Amazon, Trustpilot, Quora, Facebook, TikTok, Google SERP,
  Product Hunt per uso commerciale) sono rifiutate anche se configurate come RSS;
- in assenza di chiavi -> MOCK (source="MOCK"), mai spacciato per reale.
"""

import base64
import json
import re
import time
import urllib.parse
import zlib
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib import robotparser

from dropship.config import is_truthy
from dropship.http import DEFAULT_TIMEOUT, ExternalServiceError, urllib_transport
from dropship.models import MOCK
from dropship.problems.models import MAX_POST_CHARS, Post
from dropship.problems.text import clean_text, fold
from dropship.secrets_util import Secret

DEFAULT_CONTACT = "configura DROPSHIP_CONTACT"
APP_NAME = "dropship-problem-miner"
APP_VERSION = "0.1"
MAX_ITEMS_PER_CALL = 100

# Domini la cui raccolta automatica è vietata dai ToS o non ha base legale per noi.
DENIED_DOMAINS = {
    "amazon.": "Conditions of Use: vietati robot/data mining",
    "trustpilot.": "ToS: vietati text/data mining e scraping senza permesso",
    "quora.com": "ToS: accesso solo tramite interfacce pubblicate; nessuna API pubblica",
    "facebook.com": "Groups API dismessa (v19, 22/04/2024); scraping vietato",
    "instagram.com": "scraping vietato dai ToS Meta",
    "tiktok.com": "Research API solo ricerca non-profit; scraping vietato",
    "google.": "ToS Google vietano query automatiche (PAA/autocomplete)",
    "producthunt.com": "API: uso commerciale vietato senza permesso scritto",
    "reddit.com": "usare l'API ufficiale (OAuth), non RSS/HTML",
}


def user_agent(contact):
    return f"{APP_NAME}/{APP_VERSION} (+{contact or DEFAULT_CONTACT})"


def denied_reason(url):
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    for dom, reason in DENIED_DOMAINS.items():
        if dom.endswith("."):
            if host.startswith(dom) or f".{dom}" in f".{host}":
                return reason
        elif host == dom or host.endswith("." + dom):
            return reason
    return None


class RateLimiter:
    """Intervallo minimo tra richieste + backoff richiesto dal server. Orologio iniettabile."""

    def __init__(self, min_interval_s, clock=None, sleep=None):
        self.min_interval_s = max(0.0, float(min_interval_s))
        self._clock = clock or time.monotonic
        self._sleep = sleep or time.sleep
        self._next_allowed = None

    def wait(self):
        now = self._clock()
        if self._next_allowed is not None and now < self._next_allowed:
            self._sleep(self._next_allowed - now)
            now = self._next_allowed
        self._next_allowed = now + self.min_interval_s

    def set_interval(self, seconds):
        """Allunga l'intervallo (es. Crawl-delay scoperto dopo) anche per la prossima attesa."""
        seconds = max(0.0, float(seconds))
        if self._next_allowed is not None:
            self._next_allowed += seconds - self.min_interval_s
        self.min_interval_s = seconds

    def defer(self, seconds):
        """Il server ha chiesto di aspettare (es. ``backoff`` Stack Exchange, Retry-After)."""
        base = self._next_allowed if self._next_allowed is not None else self._clock()
        self._next_allowed = max(base, self._clock() + max(0.0, float(seconds)))


def fetch_bytes(url, *, headers, params=None, transport=None, timeout=DEFAULT_TIMEOUT,
                service="fonte", method="GET", body=None, allow_status=()):
    """GET HTTPS con decompressione gzip. Errori senza URL/query/body (possono contenere chiavi)."""
    if not isinstance(url, str) or not url.startswith("https://"):
        raise ExternalServiceError(f"{service}: solo HTTPS consentito")
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    status, raw = (transport or urllib_transport)(method, url, dict(headers), body, timeout)
    if status >= 400 and status not in allow_status:
        raise ExternalServiceError(f"{service}: HTTP {status}")
    raw = raw or b""
    if raw[:2] == b"\x1f\x8b":
        raw = _gunzip_bounded(raw, service)
    return status, raw


MAX_DECOMPRESSED_BYTES = 10 * 1024 * 1024


def _gunzip_bounded(raw, service):
    """Decompressione con tetto (difesa da gzip bomb)."""
    dec = zlib.decompressobj(16 + zlib.MAX_WBITS)
    try:
        out = dec.decompress(raw, MAX_DECOMPRESSED_BYTES + 1)
    except zlib.error:
        raise ExternalServiceError(f"{service}: risposta compressa non valida") from None
    if len(out) > MAX_DECOMPRESSED_BYTES or dec.unconsumed_tail:
        raise ExternalServiceError(f"{service}: risposta troppo grande")
    return out


def fetch_json(url, **kw):
    service = kw.get("service", "fonte")
    _, raw = fetch_bytes(url, **kw)
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise ExternalServiceError(f"{service}: risposta non JSON") from None


def _utc_from_epoch(value):
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _utc_from_iso(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _words(text):
    return set(re.findall(r"[a-z0-9]+", fold(text or "")))


def _make_post(source, platform, url, title, body, created_at, lang="", retention_days=None):
    text = clean_text(" . ".join(p for p in (title, body) if p), MAX_POST_CHARS)
    if not text or not url:
        return None  # senza testo o senza URL verificabile non è evidenza
    return Post(source=source, platform=platform, url=url, text=text, created_at=created_at,
                lang=lang, retention_days=retention_days)


class DiscussionSource(ABC):
    source = "?"
    name = "?"

    @abstractmethod
    def fetch(self, query, since=None, limit=50):
        """Restituisce una lista di ``Post`` pubblici pertinenti a ``query``."""

    def describe(self):
        return f"{self.name}: {'MOCK' if self.source == MOCK else 'reale'}"


# --------------------------------------------------------------------------- MOCK

_D = lambda y, m, d: datetime(y, m, d, 12, tzinfo=timezone.utc)  # noqa: E731

# Contenuti DIMOSTRATIVI scritti a mano: non sono post reali, URL su dominio .invalid.
MOCK_POSTS = (
    ("mock-forum-casa", _D(2026, 10, 2), "Non riesco a tenere in ordine i cavi dietro la scrivania, "
     "si aggrovigliano sempre. Qualcuno sa consigliare un organizer per cavi? Dove lo compro?"),
    ("mock-reddit-it", _D(2026, 10, 5), "Odio quando i cavi del caricabatterie si aggrovigliano sotto la "
     "scrivania, è frustrante! C'è un modo per organizzare i cavi?"),
    ("mock-stack-diy", _D(2026, 9, 28), "How do I organize the cables under my desk? They keep tangling, "
     "is there a product like a cable organizer tray?"),
    ("mock-youtube", _D(2026, 10, 8), "Come faccio a nascondere i cavi della scrivania? Consigli prodotto? "
     "Ogni giorno si aggrovigliano i cavi, non ne posso più"),
    ("mock-forum-casa", _D(2026, 10, 9), "Qualcuno sa un organizer cavi per scrivania che non si stacchi? "
     "Il mio si rompe sempre"),
    ("mock-reddit-it", _D(2026, 8, 20), "Non riesco a organizzare i cavi della scrivania in ufficio"),
    ("mock-forum-casa", _D(2026, 10, 1), "Come faccio a rinnovare il contratto della luce online? "
     "Non riesco a fare il login sull'app"),
    ("mock-reddit-it", _D(2026, 10, 3), "La borraccia termica perde sempre acqua nello zaino, "
     "qualcuno sa una borraccia che non perde?"),
    ("mock-youtube", _D(2026, 9, 25), "Odio quando i cavi dietro la TV e la scrivania si aggrovigliano, "
     "c'è un modo per nasconderli? Che prodotto mi consigliate?"),
    ("mock-forum-casa", _D(2026, 7, 30), "Come faccio a sistemare i cavi sotto la scrivania senza forare?"),
)


class MockDiscussionSource(DiscussionSource):
    source = MOCK
    name = "MOCK"

    def __init__(self, posts=None):
        self.posts = tuple(MOCK_POSTS if posts is None else posts)

    def fetch(self, query, since=None, limit=50):
        q = _words(query)
        out = []
        for i, (platform, created, text) in enumerate(self.posts):
            if since is not None and created < since:
                continue
            if q and not q & _words(text):
                continue
            post = _make_post(MOCK, platform, f"https://example.invalid/mock/{i}", "", text, created, "it")
            if post:
                out.append(post)
        return out[:limit]


# --------------------------------------------------------------------------- REDDIT

class RedditSource(DiscussionSource):
    """Reddit Data API (OAuth client credentials, solo lettura).

    Dal 11/11/2025 l'accesso richiede approvazione (Responsible Builder Policy) e
    l'uso commerciale un accordo separato: il factory lo attiva solo con
    ``REDDIT_API_APPROVED=1``. Reddit chiede di cancellare i contenuti rimossi
    e raccomanda di non conservarli oltre 48h -> retention_days=2.
    """

    source = "REDDIT"
    name = "Reddit"
    TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
    API = "https://oauth.reddit.com"
    RETENTION_DAYS = 2

    def __init__(self, client_id, client_secret, user_agent_str, subreddits=(), transport=None,
                 limiter=None):
        if not user_agent_str or not user_agent_str.strip():
            raise ValueError("Reddit richiede uno User-Agent descrittivo (REDDIT_USER_AGENT)")
        self._client_id = Secret(client_id)
        self._client_secret = Secret(client_secret)
        self.user_agent = user_agent_str.strip()
        self.subreddits = tuple(
            s.strip().strip("/").removeprefix("r/") for s in subreddits if s.strip().strip("/"))
        self._transport = transport
        self._limiter = limiter or RateLimiter(1.0)  # 100 QPM consentiti: stiamo a 60
        self._token = None
        self._token_exp = 0.0

    def __repr__(self):
        return f"RedditSource(client_id=***, subreddits={self.subreddits!r})"

    def _access_token(self):
        if self._token and time.time() < self._token_exp - 60:
            return self._token
        basic = base64.b64encode(
            f"{self._client_id.reveal()}:{self._client_secret.reveal()}".encode()).decode()
        self._limiter.wait()
        _, raw = fetch_bytes(
            self.TOKEN_URL, method="POST", transport=self._transport, service="Reddit",
            headers={"Authorization": f"Basic {basic}", "User-Agent": self.user_agent,
                     "Content-Type": "application/x-www-form-urlencoded"},
            body=b"grant_type=client_credentials",
        )
        try:
            data = json.loads(raw.decode("utf-8"))
            self._token = Secret(data["access_token"])
        except (ValueError, KeyError, TypeError, UnicodeDecodeError):
            raise ExternalServiceError("Reddit: token non ottenuto") from None
        self._token_exp = time.time() + float(data.get("expires_in") or 3600)
        return self._token

    def fetch(self, query, since=None, limit=50):
        token = self._access_token()
        path = f"/r/{'+'.join(self.subreddits)}/search" if self.subreddits else "/search"
        params = {"q": query, "sort": "new", "t": "year", "limit": min(limit, MAX_ITEMS_PER_CALL),
                  "raw_json": 1, "type": "link"}
        if self.subreddits:
            params["restrict_sr"] = 1
        self._limiter.wait()
        data = fetch_json(self.API + path, params=params, transport=self._transport, service="Reddit",
                          headers={"Authorization": f"Bearer {token.reveal()}", "User-Agent": self.user_agent,
                                   "Accept": "application/json"})
        out = []
        for child in ((data or {}).get("data") or {}).get("children") or []:
            d = (child or {}).get("data") or {}
            if d.get("over_18") or d.get("removed_by_category"):
                continue
            created = _utc_from_epoch(d.get("created_utc"))
            if since is not None and created is not None and created < since:
                continue
            permalink = d.get("permalink") or ""
            if not permalink.startswith("/r/"):
                continue
            # campi letti: title, selftext, permalink, created_utc, subreddit. MAI author.
            post = _make_post(self.source, f"reddit:r/{d.get('subreddit', '?')}",
                              "https://www.reddit.com" + permalink, d.get("title"), d.get("selftext"),
                              created, retention_days=self.RETENTION_DAYS)
            if post:
                out.append(post)
        return out


# --------------------------------------------------------------------------- STACK EXCHANGE

class StackExchangeSource(DiscussionSource):
    """Stack Exchange API 2.3 (/search/advanced). Contenuti CC BY-SA: citare con link."""

    source = "STACKEXCHANGE"
    name = "Stack Exchange"
    URL = "https://api.stackexchange.com/2.3/search/advanced"

    def __init__(self, key=None, sites=("diy", "lifehacks", "cooking", "outdoors", "parenting"),
                 contact=None, transport=None, limiter=None):
        self._key = Secret(key) if key else None
        self.sites = tuple(s.strip() for s in sites if s.strip())
        self.user_agent = user_agent(contact)
        self._transport = transport
        self._limiter = limiter or RateLimiter(0.5)

    def __repr__(self):
        return f"StackExchangeSource(key={'***' if self._key else None}, sites={self.sites!r})"

    def fetch(self, query, since=None, limit=50):
        out = []
        for site in self.sites:
            params = {"q": query, "site": site, "order": "desc", "sort": "creation",
                      "filter": "withbody", "pagesize": min(limit, MAX_ITEMS_PER_CALL)}
            if since is not None:
                params["fromdate"] = int(since.timestamp())
            if self._key:
                params["key"] = self._key.reveal()
            self._limiter.wait()
            data = fetch_json(self.URL, params=params, transport=self._transport, service="Stack Exchange",
                              headers={"User-Agent": self.user_agent, "Accept-Encoding": "gzip"})
            if isinstance(data, dict) and data.get("backoff"):
                self._limiter.defer(data["backoff"])
            for item in (data or {}).get("items") or []:
                link = item.get("link") or ""
                if not link.startswith("https://"):
                    continue
                # campi letti: title, body, link, creation_date. MAI owner.
                post = _make_post(self.source, f"stackexchange:{site}", link, item.get("title"),
                                  item.get("body"), _utc_from_epoch(item.get("creation_date")), "en")
                if post:
                    out.append(post)
        return out


# --------------------------------------------------------------------------- YOUTUBE

class YouTubeCommentsSource(DiscussionSource):
    """YouTube Data API v3: search.list (100 unità) + commentThreads.list (1 unità).

    Le Developer Policies richiedono di cancellare/aggiornare i dati non autorizzati
    entro 30 giorni -> retention_days=30. Budget quota giornaliero lato client.
    """

    source = "YOUTUBE"
    name = "YouTube"
    SEARCH = "https://www.googleapis.com/youtube/v3/search"
    COMMENTS = "https://www.googleapis.com/youtube/v3/commentThreads"
    COST_SEARCH = 100
    COST_COMMENTS = 1
    RETENTION_DAYS = 30

    def __init__(self, api_key, region="IT", language="it", videos_per_query=3, daily_quota=10000,
                 contact=None, transport=None, limiter=None):
        self._key = Secret(api_key)
        self.region = region
        self.language = language
        self.videos_per_query = max(1, int(videos_per_query))
        self.daily_quota = int(daily_quota)
        self.quota_used = 0
        self.user_agent = user_agent(contact)
        self._transport = transport
        self._limiter = limiter or RateLimiter(0.5)

    def __repr__(self):
        return f"YouTubeCommentsSource(api_key=***, region={self.region!r})"

    def _spend(self, units):
        if self.quota_used + units > self.daily_quota:
            raise ExternalServiceError("YouTube: budget quota giornaliero esaurito")
        self.quota_used += units

    def _get(self, url, params, units):
        self._spend(units)
        self._limiter.wait()
        params = dict(params, key=self._key.reveal())
        return fetch_json(url, params=params, transport=self._transport, service="YouTube",
                          headers={"User-Agent": self.user_agent, "Accept": "application/json"})

    def fetch(self, query, since=None, limit=50):
        search = {"part": "id", "q": query, "type": "video", "maxResults": self.videos_per_query,
                  "regionCode": self.region, "relevanceLanguage": self.language}
        if since is not None:
            search["publishedAfter"] = since.strftime("%Y-%m-%dT%H:%M:%SZ")
        data = self._get(self.SEARCH, search, self.COST_SEARCH)
        video_ids = [((i or {}).get("id") or {}).get("videoId") for i in (data or {}).get("items") or []]
        out = []
        per_video = max(1, min(MAX_ITEMS_PER_CALL, limit // max(1, len(video_ids) or 1)))
        for vid in filter(None, video_ids):
            try:
                cdata = self._get(self.COMMENTS, {"part": "snippet", "videoId": vid, "maxResults": per_video,
                                                  "order": "relevance", "textFormat": "plainText"},
                                  self.COST_COMMENTS)
            except ExternalServiceError as exc:
                if "quota" in str(exc):
                    raise
                continue  # commenti disattivati sul video (403): si salta
            for th in (cdata or {}).get("items") or []:
                top = ((th or {}).get("snippet") or {}).get("topLevelComment") or {}
                sn = top.get("snippet") or {}
                created = _utc_from_iso(sn.get("publishedAt"))
                if since is not None and created is not None and created < since:
                    continue
                cid = top.get("id") or ""
                url = f"https://www.youtube.com/watch?v={urllib.parse.quote(vid)}"
                if cid:
                    url += f"&lc={urllib.parse.quote(cid)}"
                # campi letti: textOriginal/textDisplay, publishedAt, id. MAI authorDisplayName/authorChannel*.
                post = _make_post(self.source, f"youtube:{vid}", url, "",
                                  sn.get("textOriginal") or sn.get("textDisplay"), created,
                                  self.language, self.RETENTION_DAYS)
                if post:
                    out.append(post)
        return out[:limit]


# --------------------------------------------------------------------------- HACKER NEWS

class HackerNewsSource(DiscussionSource):
    """HN Search API di Algolia (pubblica, senza chiave; ~10.000 req/h per IP, fonte terza)."""

    source = "HACKERNEWS"
    name = "Hacker News"
    URL = "https://hn.algolia.com/api/v1/search_by_date"

    def __init__(self, contact=None, transport=None, limiter=None):
        self.user_agent = user_agent(contact)
        self._transport = transport
        self._limiter = limiter or RateLimiter(1.0)

    def fetch(self, query, since=None, limit=50):
        params = {"query": query, "tags": "(story,comment)", "hitsPerPage": min(limit, MAX_ITEMS_PER_CALL)}
        if since is not None:
            params["numericFilters"] = f"created_at_i>{int(since.timestamp())}"
        self._limiter.wait()
        data = fetch_json(self.URL, params=params, transport=self._transport, service="Hacker News",
                          headers={"User-Agent": self.user_agent, "Accept": "application/json"})
        out = []
        for hit in (data or {}).get("hits") or []:
            oid = str(hit.get("objectID") or "")
            if not oid.isdigit():
                continue
            # campi letti: title, story_text, comment_text, created_at_i, objectID. MAI author.
            post = _make_post(self.source, "hackernews", f"https://news.ycombinator.com/item?id={oid}",
                              hit.get("title"), hit.get("comment_text") or hit.get("story_text"),
                              _utc_from_epoch(hit.get("created_at_i")), "en")
            if post:
                out.append(post)
        return out


# --------------------------------------------------------------------------- RSS / ATOM

_ATOM = "{http://www.w3.org/2005/Atom}"
_CONTENT = "{http://purl.org/rss/1.0/modules/content/}encoded"
MAX_FEED_BYTES = 2 * 1024 * 1024


def _parse_date(value):
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value.strip())
    except (TypeError, ValueError, IndexError):
        return _utc_from_iso(value.strip())
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def parse_feed(raw):
    """RSS 2.0 / Atom -> lista di dict(title, body, link, created_at). Rifiuta DTD/entità (XXE, billion laughs)."""
    if len(raw) > MAX_FEED_BYTES:
        raise ExternalServiceError("RSS: feed troppo grande")
    head = raw[:4096].lower()
    if b"<!doctype" in head or b"<!entity" in raw.lower():
        raise ExternalServiceError("RSS: DTD/entità non ammesse")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        raise ExternalServiceError("RSS: XML non valido") from None
    items = []
    for it in root.iter("item"):
        items.append({
            "title": (it.findtext("title") or "").strip(),
            "body": it.findtext(_CONTENT) or it.findtext("description") or "",
            "link": (it.findtext("link") or "").strip(),
            "created_at": _parse_date(it.findtext("pubDate")),
        })
    for en in root.iter(f"{_ATOM}entry"):
        link = ""
        for ln in en.findall(f"{_ATOM}link"):
            if ln.get("rel", "alternate") == "alternate" and ln.get("href"):
                link = ln.get("href")
                break
        items.append({
            "title": (en.findtext(f"{_ATOM}title") or "").strip(),
            "body": en.findtext(f"{_ATOM}content") or en.findtext(f"{_ATOM}summary") or "",
            "link": link.strip(),
            "created_at": _utc_from_iso(en.findtext(f"{_ATOM}published") or en.findtext(f"{_ATOM}updated")),
        })
    return items


class RssSource(DiscussionSource):
    """Feed RSS/Atom pubblicati dai siti (forum, Discourse ``/latest.rss``, sezioni domande).

    - solo feed elencati esplicitamente (``DROPSHIP_PROBLEM_RSS_FEEDS``) dopo verifica
      manuale dei termini del sito;
    - domini vietati rifiutati (``DENIED_DOMAINS``);
    - robots.txt rispettato (anche Crawl-delay); 401/403/5xx su robots -> non si legge.
    """

    source = "RSS"
    name = "RSS/Atom"

    def __init__(self, feeds, contact=None, transport=None, min_interval_s=5.0, clock=None, sleep=None):
        self.feeds = tuple(f.strip() for f in feeds if f and f.strip())
        self.user_agent = user_agent(contact)
        self._transport = transport
        self._clock, self._sleep = clock, sleep
        self._min_interval = min_interval_s
        self._limiters = {}
        self._robots = {}
        self.skipped = []  # (feed, motivo) — visibile nel report, mai silenzioso

    def _limiter(self, host, crawl_delay=None):
        lim = self._limiters.get(host)
        if lim is None:
            lim = self._limiters[host] = RateLimiter(self._min_interval, self._clock, self._sleep)
        if crawl_delay:
            lim.set_interval(max(lim.min_interval_s, float(crawl_delay)))
        return lim

    def _robots_allows(self, url):
        parts = urllib.parse.urlsplit(url)
        host = parts.netloc.lower()
        if host not in self._robots:
            robots_url = f"https://{host}/robots.txt"
            self._limiter(host).wait()
            try:
                status, raw = fetch_bytes(robots_url, transport=self._transport, service="robots.txt",
                                          headers={"User-Agent": self.user_agent},
                                          allow_status=tuple(range(400, 600)))
            except ExternalServiceError:
                status, raw = 503, b""
            rp = robotparser.RobotFileParser()
            if status in (401, 403) or status >= 500:
                rp.disallow_all = True
            elif status >= 400:
                rp.allow_all = True
            else:
                rp.parse(raw.decode("utf-8", "replace").splitlines())
            self._robots[host] = rp
        rp = self._robots[host]
        delay = rp.crawl_delay(APP_NAME) if not (rp.allow_all or rp.disallow_all) else None
        self._limiter(host, delay)
        return rp.can_fetch(APP_NAME, url)

    def fetch(self, query, since=None, limit=50):
        q = _words(query)
        out = []
        for feed in self.feeds:
            if not feed.startswith("https://"):
                self.skipped.append((feed, "solo HTTPS"))
                continue
            reason = denied_reason(feed)
            if reason:
                self.skipped.append((feed, f"dominio non ammesso: {reason}"))
                continue
            if not self._robots_allows(feed):
                self.skipped.append((feed, "vietato da robots.txt"))
                continue
            host = urllib.parse.urlsplit(feed).netloc.lower()
            self._limiter(host).wait()
            _, raw = fetch_bytes(feed, transport=self._transport, service="RSS",
                                 headers={"User-Agent": self.user_agent,
                                          "Accept": "application/rss+xml, application/atom+xml, application/xml"})
            for item in parse_feed(raw):
                if since is not None and item["created_at"] is not None and item["created_at"] < since:
                    continue
                if not item["link"].startswith("https://"):
                    continue
                post = _make_post(self.source, f"rss:{host}", item["link"], item["title"], item["body"],
                                  item["created_at"])
                if post is None:
                    continue
                if q and not q & _words(post.text):
                    continue
                out.append(post)
        return out[:limit]


# --------------------------------------------------------------------------- FACTORY

def _csv(value):
    return tuple(v.strip() for v in str(value or "").split(",") if v.strip())


def build_discussion_sources(env, transport=None):
    """Fonti reali solo se configurate; altrimenti [MockDiscussionSource]. Mai mescolare per errore:
    se c'è almeno una fonte reale, il MOCK NON viene aggiunto."""
    if is_truthy(env.get("DROPSHIP_FORCE_MOCK")):
        return [MockDiscussionSource()]
    contact = env.get("DROPSHIP_CONTACT") or None
    out = []
    if (env.get("REDDIT_CLIENT_ID") and env.get("REDDIT_CLIENT_SECRET") and env.get("REDDIT_USER_AGENT")
            and is_truthy(env.get("REDDIT_API_APPROVED"))):
        out.append(RedditSource(env["REDDIT_CLIENT_ID"], env["REDDIT_CLIENT_SECRET"], env["REDDIT_USER_AGENT"],
                                _csv(env.get("REDDIT_SUBREDDITS")), transport=transport))
    if env.get("STACKEXCHANGE_KEY") or is_truthy(env.get("DROPSHIP_ENABLE_STACKEXCHANGE")):
        sites = _csv(env.get("STACKEXCHANGE_SITES")) or ("diy", "lifehacks", "cooking", "outdoors", "parenting")
        out.append(StackExchangeSource(env.get("STACKEXCHANGE_KEY") or None, sites, contact, transport))
    if env.get("YOUTUBE_API_KEY"):
        out.append(YouTubeCommentsSource(env["YOUTUBE_API_KEY"],
                                         daily_quota=int(env.get("YOUTUBE_DAILY_QUOTA") or 10000),
                                         contact=contact, transport=transport))
    if is_truthy(env.get("DROPSHIP_ENABLE_HN")):
        out.append(HackerNewsSource(contact, transport))
    feeds = _csv(env.get("DROPSHIP_PROBLEM_RSS_FEEDS"))
    if feeds:
        out.append(RssSource(feeds, contact, transport))
    return out or [MockDiscussionSource()]


def describe_discussion_sources(env):
    """Righe leggibili sullo stato delle fonti, senza mai stampare chiavi."""
    lines = []
    for src in build_discussion_sources(env):
        lines.append(src.describe())
    if env.get("REDDIT_CLIENT_ID") and not is_truthy(env.get("REDDIT_API_APPROVED")):
        lines.append("Reddit: credenziali presenti ma REDDIT_API_APPROVED non impostato -> disattivato")
    return lines
