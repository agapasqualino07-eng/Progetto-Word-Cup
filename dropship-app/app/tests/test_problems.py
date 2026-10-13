"""Test del problem-mining. Nessuna chiamata di rete: FakeTransport ovunque."""

import gzip
import json
import unittest
from datetime import datetime, timedelta, timezone

from dropship.config import ConfigError
from dropship.http import ExternalServiceError
from dropship.problems import (
    HackerNewsSource,
    MockDiscussionSource,
    RedditSource,
    RssSource,
    StackExchangeSource,
    YouTubeCommentsSource,
    build_discussion_sources,
    describe_discussion_sources,
    format_report,
    load_problem_thresholds,
    mine_problems,
)
from dropship.problems.cluster import cluster_mentions
from dropship.problems.extract import dedupe, extract_mentions, physical_score, purchase_intent
from dropship.problems.models import Evidence, Post
from dropship.problems.scoring import OPPORTUNITY, SKIP, WATCH, ProblemThresholds, evaluate_cluster, growth_rate
from dropship.problems.sources import RateLimiter, denied_reason, parse_feed
from dropship.problems.text import clean_text, fold, tokenize
from tests.helpers import FakeTransport

NOW = datetime(2026, 10, 13, 12, tzinfo=timezone.utc)


def post(text, platform="forum-a", url=None, days_ago=3, source="TEST"):
    created = None if days_ago is None else NOW - timedelta(days=days_ago)
    return Post(source=source, platform=platform, url=url or f"https://example.org/{abs(hash((text, platform)))}",
                text=text, created_at=created)


class FakeClock:
    def __init__(self):
        self.t = 0.0
        self.slept = []

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.slept.append(round(s, 3))
        self.t += s


# --------------------------------------------------------------------------- testo e privacy

class TestTextAndPrivacy(unittest.TestCase):
    def test_redacts_personal_data(self):
        raw = "Scrivimi a mario.rossi@gmail.com o @mario_r o u/mario88, tel +39 333 123 4567, vedi https://x.it/a?b=1"
        out = clean_text(raw, 500)
        for leaked in ("mario.rossi", "@mario_r", "u/mario88", "333 123", "https://x.it"):
            self.assertNotIn(leaked, out)
        self.assertIn("[email]", out)
        self.assertIn("[utente]", out)
        self.assertIn("[numero]", out)

    def test_strips_html_and_quoted_text(self):
        out = clean_text("<p>Il mio problema</p><blockquote>citazione di altri</blockquote><script>x()</script>", 500)
        self.assertIn("Il mio problema", out)
        self.assertNotIn("citazione", out)
        self.assertNotIn("x()", out)

    def test_truncates_to_minimum_text(self):
        self.assertLessEqual(len(clean_text("a" * 5000, 100)), 100)

    def test_post_model_has_no_author_field(self):
        self.assertNotIn("author", Post.__dataclass_fields__)
        self.assertNotIn("username", Post.__dataclass_fields__)

    def test_tokenize_folds_accents_and_stems_bilingual(self):
        self.assertEqual(fold("Perché È così"), "perche e cosi")
        self.assertEqual(tokenize("organizzare")[0], tokenize("organizer")[0])
        self.assertEqual(tokenize("cavi"), tokenize("cavo"))
        self.assertEqual(tokenize("cables"), tokenize("cable"))


# --------------------------------------------------------------------------- estrazione

class TestExtraction(unittest.TestCase):
    def test_italian_patterns(self):
        for text in ("Non riesco a tenere fermi i cavi", "Come faccio a pulire il filtro?",
                     "Qualcuno sa come fissare la mensola?", "Odio quando la borraccia perde",
                     "Il gancio si rompe sempre", "C'è un modo per asciugare le scarpe?",
                     "Ce un modo per fermare il tappetino"):
            self.assertTrue(extract_mentions(post(text)), text)

    def test_english_patterns(self):
        for text in ("How do I stop my cables from tangling?", "Is there a product to hold the phone?",
                     "My shower caddy keeps breaking", "I hate when the lamp falls"):
            self.assertTrue(extract_mentions(post(text)), text)

    def test_non_problem_text_ignored(self):
        self.assertEqual(extract_mentions(post("Bellissima giornata al mare con gli amici")), [])

    def test_purchase_intent(self):
        self.assertTrue(purchase_intent(fold("Dove lo compro?")))
        self.assertTrue(purchase_intent(fold("Consigli prodotto per i cavi")))
        self.assertTrue(purchase_intent(fold("Is there a product for this")))
        self.assertTrue(purchase_intent(fold("where can I buy one")))
        self.assertFalse(purchase_intent(fold("non riesco a dormire")))

    def test_physical_solvability(self):
        self.assertGreater(physical_score(fold("organizer per cavi della scrivania")), 0.5)
        self.assertEqual(physical_score(fold("non riesco a fare il login sull'app")), 0.0)
        self.assertLess(physical_score(fold("app per cavi")), physical_score(fold("organizer per cavi")))
        # "app" non deve scattare dentro "appena"
        self.assertGreater(physical_score(fold("appena comprato un organizer per cavi")), 0.5)

    def test_intent_from_context_sentence(self):
        ms = extract_mentions(post("Non riesco a tenere in ordine i cavi. Dove lo compro un organizer?"))
        self.assertTrue(all(m.purchase_intent for m in ms))

    def test_dedupe_crosspost_and_same_post(self):
        a = post("Non riesco a organizzare i cavi della scrivania", platform="forum-a", url="https://a.org/1",
                 days_ago=5)
        b = post("Non riesco a organizzare i cavi della scrivania!", platform="forum-b", url="https://b.org/9",
                 days_ago=1)
        ms = extract_mentions(a) + extract_mentions(b) + extract_mentions(a)
        kept = dedupe(ms)
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0].post.url, "https://a.org/1")  # tiene la più vecchia


# --------------------------------------------------------------------------- clustering e scoring

def mentions_for(texts_platforms):
    out = []
    for i, (text, platform, days) in enumerate(texts_platforms):
        out.extend(extract_mentions(post(text, platform, f"https://example.org/{platform}/{i}", days)))
    return dedupe(out)


CABLE_POSTS = [
    ("Non riesco a organizzare i cavi della scrivania, dove lo compro un organizer?", "forum-a", 2),
    ("Odio quando i cavi della scrivania si aggrovigliano!", "forum-b", 5),
    ("Come faccio a nascondere i cavi sotto la scrivania? Consigli prodotto?", "forum-c", 8),
    ("Qualcuno sa un organizer per i cavi della scrivania?", "forum-a", 10),
    ("C'è un modo per tenere i cavi della scrivania in ordine?", "forum-b", 12),
    ("I cavi della scrivania si aggrovigliano sempre, non ne posso più", "forum-c", 45),
]


class TestClusteringAndScoring(unittest.TestCase):
    def test_similar_problems_cluster_together_unrelated_apart(self):
        ms = mentions_for(CABLE_POSTS + [("La borraccia termica perde sempre acqua nello zaino", "forum-a", 3)])
        clusters = cluster_mentions(ms, similarity=0.2)
        biggest = max(clusters, key=lambda c: len(c.mentions))
        self.assertGreaterEqual(len({m.post.url for m in biggest.mentions}), 5)
        self.assertTrue(all("borrac" not in " ".join(m.tokens) for m in biggest.mentions))
        self.assertIn("cav", biggest.keywords)

    def test_strong_multi_source_problem_is_opportunity(self):
        th = ProblemThresholds()
        cl = max(cluster_mentions(mentions_for(CABLE_POSTS), 0.2), key=lambda c: len(c.mentions))
        opp = evaluate_cluster(cl, NOW, th)
        self.assertEqual(opp.status, OPPORTUNITY, opp.reasons)
        self.assertEqual(opp.confidence, "ALTA")
        self.assertEqual(opp.score.source_count, 3)
        self.assertGreater(opp.score.purchase_intent, 0.3)

    def test_too_few_evidence_is_skip(self):
        cl = cluster_mentions(mentions_for(CABLE_POSTS[:3]), 0.2)[0]
        opp = evaluate_cluster(cl, NOW, ProblemThresholds())
        self.assertEqual(opp.status, SKIP)
        self.assertEqual(opp.confidence, "INSUFFICIENTE")
        self.assertIn("evidenze insufficienti", opp.reasons[0])

    def test_single_source_is_penalised_and_not_opportunity(self):
        single = [(t, "forum-a", d) for t, _, d in CABLE_POSTS]
        cl = max(cluster_mentions(mentions_for(single), 0.2), key=lambda c: len(c.mentions))
        multi = max(cluster_mentions(mentions_for(CABLE_POSTS), 0.2), key=lambda c: len(c.mentions))
        th = ProblemThresholds()
        o1, o3 = evaluate_cluster(cl, NOW, th), evaluate_cluster(multi, NOW, th)
        self.assertEqual(o1.status, WATCH)
        self.assertEqual(o1.confidence, "BASSA")
        self.assertLess(o1.score.total, o3.score.total)

    def test_non_physical_problem_is_skip(self):
        texts = ["Non riesco a fare il login sull'app della banca", "Come faccio a recuperare la password dell'account?",
                 "Qualcuno sa perché l'app della banca non funziona più?", "Non riesco a entrare nell'account email",
                 "C'è un modo per cambiare password senza app?", "Non riesco a fare il login sul sito, account bloccato"]
        posts = [(t, f"f{i % 3}", i) for i, t in enumerate(texts)]
        cl = max(cluster_mentions(mentions_for(posts), 0.2), key=lambda c: len(c.mentions))
        opp = evaluate_cluster(cl, NOW, ProblemThresholds(min_evidence=2))
        self.assertEqual(opp.status, SKIP)
        self.assertIn("prodotto fisico", opp.reasons[0])

    def test_growth_rate(self):
        ms = mentions_for([("Non riesco a fissare la mensola", "a", 5), ("Non riesco a fissare la mensola bene", "b", 10),
                           ("Non riesco a fissare la mensola di legno", "c", 40)])
        self.assertAlmostEqual(growth_rate(ms, NOW, 30), 1.0)
        undated = [m for m in extract_mentions(post("Non riesco a fissare la mensola", days_ago=None))]
        self.assertIsNone(growth_rate(undated, NOW, 30))

    def test_missing_dates_are_reported_not_invented(self):
        ms = [m for i in range(5) for m in extract_mentions(
            post(f"Non riesco a fissare la mensola {i}", f"p{i % 2}", f"https://e.org/{i}", None))]
        opp = evaluate_cluster(cluster_mentions(ms, 0.2)[0], NOW, ProblemThresholds())
        self.assertIsNone(opp.score.growth)
        self.assertTrue(any("DATO MANCANTE" in r for r in opp.reasons))
        self.assertTrue(all(e.date == "DATO MANCANTE" for e in opp.evidence))

    def test_thresholds_from_env_and_validation(self):
        th = load_problem_thresholds({"DROPSHIP_PROBLEM_MIN_EVIDENCE": "8", "DROPSHIP_PROBLEM_MIN_SCORE": "70"})
        self.assertEqual((th.min_evidence, th.min_score), (8, 70.0))
        for bad in ({"DROPSHIP_PROBLEM_MIN_EVIDENCE": "1"}, {"DROPSHIP_PROBLEM_MIN_SCORE": "150"},
                    {"DROPSHIP_PROBLEM_MIN_PHYSICAL": "0"}, {"DROPSHIP_PROBLEM_MIN_SOURCES": "x"}):
            with self.assertRaises(ConfigError):
                load_problem_thresholds(bad)

    def test_custom_threshold_changes_decision(self):
        cl = max(cluster_mentions(mentions_for(CABLE_POSTS), 0.2), key=lambda c: len(c.mentions))
        self.assertEqual(evaluate_cluster(cl, NOW, ProblemThresholds(min_score=99)).status, WATCH)
        self.assertEqual(evaluate_cluster(cl, NOW, ProblemThresholds(min_evidence=50)).status, SKIP)


# --------------------------------------------------------------------------- evidenze

class TestEvidence(unittest.TestCase):
    def test_evidence_comes_only_from_real_posts(self):
        cl = max(cluster_mentions(mentions_for(CABLE_POSTS), 0.2), key=lambda c: len(c.mentions))
        opp = evaluate_cluster(cl, NOW, ProblemThresholds())
        urls = {m.post.url for m in cl.mentions}
        self.assertTrue(opp.evidence)
        for e in opp.evidence:
            self.assertIn(e.url, urls)
            self.assertTrue(any(e.excerpt.rstrip("…") in m.post.text for m in cl.mentions))
            self.assertLessEqual(len(e.excerpt), 200)
        self.assertEqual(len({e.platform for e in opp.evidence[:3]}), 3)  # varietà di fonti prima

    def test_retention_from_collection_date(self):
        p = Post("REDDIT", "reddit:r/x", "https://www.reddit.com/r/x/comments/1/t/", "Non riesco a fissare la mensola",
                 NOW - timedelta(days=100), retention_days=2)
        ev = Evidence.from_mention(extract_mentions(p)[0], NOW)
        self.assertEqual(ev.retain_until, (NOW + timedelta(days=2)).date().isoformat())

    def test_mock_is_flagged_never_real(self):
        report = mine_problems([MockDiscussionSource()], ["cavi"], now=NOW)
        self.assertTrue(report.opportunities)
        for o in report.opportunities:
            self.assertTrue(o.is_mock)
            self.assertTrue(all(e.source == "MOCK" and ".invalid/" in e.url for e in o.evidence))
        self.assertIn("[MOCK]", format_report(report))


# --------------------------------------------------------------------------- adapter reali (senza rete)

class TestRedditAdapter(unittest.TestCase):
    def test_oauth_search_no_author_and_filters(self):
        listing = {"data": {"children": [
            {"data": {"title": "Non riesco a organizzare i cavi", "selftext": "aiuto, u/pippo dice di no",
                      "permalink": "/r/italy/comments/abc/cavi/", "created_utc": NOW.timestamp() - 3600,
                      "subreddit": "italy", "author": "mario_rossi_88"}},
            {"data": {"title": "nsfw", "selftext": "", "permalink": "/r/x/comments/1/", "over_18": True,
                      "created_utc": NOW.timestamp(), "subreddit": "x", "author": "y"}},
        ]}}
        t = FakeTransport([(200, {"access_token": "TOK", "expires_in": 3600}), (200, listing)])
        src = RedditSource("cid", "csecret", "web:dropship-miner:0.1 (by /u/test)", ["r/italy"], transport=t,
                           limiter=RateLimiter(0))
        posts = src.fetch("cavi")
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].url, "https://www.reddit.com/r/italy/comments/abc/cavi/")
        self.assertNotIn("mario_rossi_88", repr(posts[0]))
        self.assertNotIn("pippo", posts[0].text)
        self.assertEqual(posts[0].retention_days, 2)
        self.assertEqual(t.calls[0]["method"], "POST")
        self.assertTrue(t.calls[1]["url"].startswith("https://oauth.reddit.com/r/italy/search?"))
        self.assertIn("restrict_sr=1", t.calls[1]["url"])
        self.assertEqual(t.calls[1]["headers"]["User-Agent"], "web:dropship-miner:0.1 (by /u/test)")
        self.assertNotIn("csecret", repr(src))

    def test_requires_user_agent(self):
        with self.assertRaises(ValueError):
            RedditSource("a", "b", "  ")

    def test_subreddit_names_kept_intact(self):
        src = RedditSource("a", "b", "ua", ["r/rome", "/r/italy/", "relationships"])
        self.assertEqual(src.subreddits, ("rome", "italy", "relationships"))


class TestStackExchangeAdapter(unittest.TestCase):
    def test_gzip_backoff_and_fields(self):
        payload = {"items": [{"title": "How do I stop cables tangling?", "body": "<p>They keep tangling</p>",
                              "link": "https://diy.stackexchange.com/questions/1/x", "creation_date": 1790000000,
                              "owner": {"display_name": "SECRET_NAME"}}], "backoff": 10}
        t = FakeTransport([(200, gzip.compress(json.dumps(payload).encode()))])
        clock = FakeClock()
        lim = RateLimiter(0, clock=clock, sleep=clock.sleep)
        src = StackExchangeSource(key="SEKEY", sites=["diy"], contact="ops@example.org", transport=t, limiter=lim)
        posts = src.fetch("cables")
        self.assertEqual(len(posts), 1)
        self.assertNotIn("SECRET_NAME", repr(posts[0]))
        self.assertEqual(posts[0].platform, "stackexchange:diy")
        self.assertIn("ops@example.org", t.calls[0]["headers"]["User-Agent"])
        lim.wait()  # il backoff del server va rispettato
        self.assertEqual(clock.slept, [10.0])
        self.assertNotIn("SEKEY", repr(src))


    def test_gzip_bomb_rejected(self):
        bomb = gzip.compress(b"0" * (11 * 1024 * 1024))
        src = StackExchangeSource(sites=["diy"], transport=FakeTransport([(200, bomb)]), limiter=RateLimiter(0))
        with self.assertRaises(ExternalServiceError):
            src.fetch("x")


class TestYouTubeAdapter(unittest.TestCase):
    def test_search_then_comments_quota_and_no_author(self):
        search = {"items": [{"id": {"videoId": "VID1"}}]}
        comments = {"items": [{"snippet": {"topLevelComment": {"id": "C1", "snippet": {
            "textOriginal": "Odio quando i cavi si aggrovigliano", "publishedAt": "2026-10-01T10:00:00Z",
            "authorDisplayName": "Utente Vero", "authorChannelUrl": "https://youtube.com/@vero"}}}}]}
        t = FakeTransport([(200, search), (200, comments)])
        src = YouTubeCommentsSource("YTKEY", transport=t, limiter=RateLimiter(0))
        posts = src.fetch("cavi scrivania")
        self.assertEqual(src.quota_used, 101)
        self.assertEqual(posts[0].url, "https://www.youtube.com/watch?v=VID1&lc=C1")
        self.assertNotIn("Utente Vero", repr(posts[0]))
        self.assertEqual(posts[0].retention_days, 30)
        self.assertIn("relevanceLanguage=it", t.calls[0]["url"])

    def test_quota_budget_enforced_without_calling(self):
        t = FakeTransport()
        src = YouTubeCommentsSource("K", daily_quota=50, transport=t, limiter=RateLimiter(0))
        with self.assertRaises(ExternalServiceError):
            src.fetch("x")
        self.assertEqual(t.calls, [])

    def test_error_does_not_leak_key(self):
        t = FakeTransport([(403, b'{"error":"key YTKEY invalid"}')])
        src = YouTubeCommentsSource("YTKEY", transport=t, limiter=RateLimiter(0))
        with self.assertRaises(ExternalServiceError) as ctx:
            src.fetch("x")
        self.assertNotIn("YTKEY", str(ctx.exception))


class TestHackerNewsAdapter(unittest.TestCase):
    def test_hits_to_posts(self):
        t = FakeTransport([(200, {"hits": [
            {"objectID": "123", "comment_text": "Is there a product to keep cables tidy?", "created_at_i": 1790000000,
             "author": "pg"},
            {"objectID": "bad", "title": "x"}]})])
        posts = HackerNewsSource(transport=t, limiter=RateLimiter(0)).fetch("cables", since=NOW - timedelta(days=30))
        self.assertEqual([p.url for p in posts], ["https://news.ycombinator.com/item?id=123"])
        self.assertIn("numericFilters=created_at_i", t.calls[0]["url"])


RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Come faccio a fissare la mensola?</title><link>https://forum.example.it/t/1</link>
<description>&lt;p&gt;Si stacca sempre, scrivete a a@b.it&lt;/p&gt;</description>
<pubDate>Wed, 07 Oct 2026 10:00:00 +0200</pubDate></item>
<item><title>Vendo bici</title><link>https://forum.example.it/t/2</link><description>ok</description></item>
</channel></rss>"""

ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Non riesco a pulire il filtro</title><link rel="alternate" href="https://d.example.org/t/9"/>
<published>2026-10-01T08:00:00Z</published><summary>aiuto</summary></entry></feed>"""


class TestRssAdapter(unittest.TestCase):
    def _src(self, feeds, responses):
        clock = FakeClock()
        t = FakeTransport(responses)
        return RssSource(feeds, contact="ops@example.org", transport=t, min_interval_s=5, clock=clock,
                         sleep=clock.sleep), t, clock

    def test_parse_rss_and_atom(self):
        items = parse_feed(RSS) + parse_feed(ATOM)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["created_at"], datetime(2026, 10, 7, 8, tzinfo=timezone.utc))
        self.assertEqual(items[2]["link"], "https://d.example.org/t/9")

    def test_rejects_dtd_entities(self):
        evil = b'<?xml version="1.0"?><!DOCTYPE r [<!ENTITY a "aaaa">]><rss><channel></channel></rss>'
        with self.assertRaises(ExternalServiceError):
            parse_feed(evil)

    def test_respects_robots_and_rate_limit(self):
        src, t, clock = self._src(["https://forum.example.it/feed.rss"],
                                  [(200, b"User-agent: *\nCrawl-delay: 10\nAllow: /\n"), (200, RSS)])
        posts = src.fetch("mensola")
        self.assertEqual(len(posts), 1)  # "Vendo bici" filtrato dalla query
        self.assertNotIn("a@b.it", posts[0].text)
        self.assertEqual(t.calls[0]["url"], "https://forum.example.it/robots.txt")
        self.assertEqual(clock.slept, [10.0])  # crawl-delay rispettato tra robots e feed

    def test_robots_disallow_skips_feed(self):
        src, t, _ = self._src(["https://forum.example.it/feed.rss"], [(200, b"User-agent: *\nDisallow: /\n")])
        self.assertEqual(src.fetch(""), [])
        self.assertEqual(len(t.calls), 1)
        self.assertIn("robots", src.skipped[0][1])

    def test_robots_403_means_no(self):
        src, t, _ = self._src(["https://forum.example.it/feed.rss"], [(403, b"")])
        self.assertEqual(src.fetch(""), [])
        self.assertEqual(len(t.calls), 1)

    def test_denied_domains_never_fetched(self):
        feeds = ["https://www.amazon.it/rss/x", "https://it.trustpilot.com/review/x", "https://www.quora.com/feed",
                 "https://www.facebook.com/groups/1/feed", "https://www.reddit.com/r/italy/.rss",
                 "http://forum.example.it/feed"]
        src, t, _ = self._src(feeds, [])
        self.assertEqual(src.fetch(""), [])
        self.assertEqual(t.calls, [])
        self.assertEqual(len(src.skipped), len(feeds))
        self.assertIsNone(denied_reason("https://forum.example.it/feed"))
        self.assertIsNone(denied_reason("https://www.googlefans.example.org/feed"))


class TestRateLimiter(unittest.TestCase):
    def test_min_interval(self):
        clock = FakeClock()
        lim = RateLimiter(2.0, clock=clock, sleep=clock.sleep)
        lim.wait()
        lim.wait()
        clock.t += 5
        lim.wait()
        self.assertEqual(clock.slept, [2.0])


# --------------------------------------------------------------------------- factory e pipeline

class TestFactoryAndPipeline(unittest.TestCase):
    def test_no_keys_means_mock_only(self):
        srcs = build_discussion_sources({})
        self.assertEqual(len(srcs), 1)
        self.assertIsInstance(srcs[0], MockDiscussionSource)

    def test_reddit_needs_explicit_approval_flag(self):
        env = {"REDDIT_CLIENT_ID": "a", "REDDIT_CLIENT_SECRET": "SEGRETO", "REDDIT_USER_AGENT": "ua"}
        self.assertIsInstance(build_discussion_sources(env)[0], MockDiscussionSource)
        text = "\n".join(describe_discussion_sources(env))
        self.assertIn("REDDIT_API_APPROVED", text)
        self.assertNotIn("SEGRETO", text)
        env["REDDIT_API_APPROVED"] = "1"
        self.assertIsInstance(build_discussion_sources(env)[0], RedditSource)

    def test_real_sources_selected_and_mock_not_mixed(self):
        env = {"STACKEXCHANGE_KEY": "k", "YOUTUBE_API_KEY": "k", "DROPSHIP_ENABLE_HN": "1",
               "DROPSHIP_PROBLEM_RSS_FEEDS": "https://forum.example.it/feed.rss"}
        kinds = {type(s) for s in build_discussion_sources(env)}
        self.assertEqual(kinds, {StackExchangeSource, YouTubeCommentsSource, HackerNewsSource, RssSource})
        env["DROPSHIP_FORCE_MOCK"] = "1"
        self.assertIsInstance(build_discussion_sources(env)[0], MockDiscussionSource)

    def test_source_failure_degrades_gracefully(self):
        class Broken(MockDiscussionSource):
            name = "Rotta"

            def fetch(self, query, since=None, limit=50):
                raise ExternalServiceError("Rotta: HTTP 503")

        report = mine_problems([Broken(), MockDiscussionSource()], ["cavi"], now=NOW)
        self.assertEqual(report.errors, [("Rotta", "Rotta: HTTP 503")])
        self.assertTrue(report.actionable)

    def test_end_to_end_mock_ranking(self):
        report = mine_problems([MockDiscussionSource()], ["cavi", "borraccia", "contratto"], now=NOW)
        statuses = [o.status for o in report.opportunities]
        self.assertEqual(statuses, sorted(statuses, key=[OPPORTUNITY, WATCH, SKIP].index))
        top = report.opportunities[0]
        self.assertEqual(top.status, OPPORTUNITY)
        self.assertIn("cav", top.keywords)
        # il problema software (login/contratto) non diventa mai un'opportunità
        self.assertFalse(any(o.status != SKIP and ("login" in o.label or "contra" in o.label)
                             for o in report.opportunities))
        text = format_report(report)
        self.assertIn("example.invalid", text)


if __name__ == "__main__":
    unittest.main()
