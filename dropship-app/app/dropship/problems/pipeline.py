"""Pipeline: fonti -> post -> frasi-problema -> dedup -> cluster -> score -> opportunità."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from dropship.http import ExternalServiceError
from dropship.problems.cluster import cluster_mentions
from dropship.problems.extract import dedupe, extract_mentions
from dropship.problems.scoring import OPPORTUNITY, SKIP, WATCH, ProblemThresholds, evaluate_cluster

_ORDER = {OPPORTUNITY: 0, WATCH: 1, SKIP: 2}


@dataclass
class MiningReport:
    opportunities: list = field(default_factory=list)  # ordinate: OPPORTUNITA, DA MONITORARE, SKIP; poi score
    errors: list = field(default_factory=list)  # (fonte, messaggio senza segreti)
    skipped_feeds: list = field(default_factory=list)
    posts_seen: int = 0
    mentions_kept: int = 0

    @property
    def actionable(self):
        return [o for o in self.opportunities if o.status == OPPORTUNITY]


def mine_problems(sources, queries, now=None, thresholds=None, lookback_days=180, limit_per_query=50):
    now = now or datetime.now(timezone.utc)
    th = thresholds or ProblemThresholds()
    since = now - timedelta(days=lookback_days)
    report = MiningReport()
    posts = []
    for src in sources:
        for q in queries:
            try:
                posts.extend(src.fetch(q, since=since, limit=limit_per_query))
            except ExternalServiceError as exc:
                # degrada con grazia: la fonte manca, il resto continua; nessun dato inventato
                report.errors.append((src.name, str(exc)))
                break
        report.skipped_feeds.extend(getattr(src, "skipped", ()))
    report.posts_seen = len(posts)
    mentions = []
    for p in posts:
        mentions.extend(extract_mentions(p))
    mentions = dedupe(mentions)
    report.mentions_kept = len(mentions)
    clusters = cluster_mentions(mentions, similarity=th.cluster_similarity)
    opps = [evaluate_cluster(c, now, th) for c in clusters]
    opps.sort(key=lambda o: (_ORDER[o.status], -o.score.total, o.label))
    report.opportunities = opps
    return report


def format_report(report):
    """Testo leggibile (italiano). Ogni opportunità mostra le citazioni con fonte, URL, data."""
    lines = [f"Post analizzati: {report.posts_seen} · frasi-problema uniche: {report.mentions_kept}"]
    for name, msg in report.errors:
        lines.append(f"! {name}: {msg} (fonte esclusa da questo giro)")
    for feed, why in report.skipped_feeds:
        lines.append(f"! feed saltato: {feed} — {why}")
    for o in report.opportunities:
        if o.status == SKIP:
            continue
        s = o.score
        growth = "DATO MANCANTE" if s.growth is None else f"{s.growth:+.0%}"
        tag = " [MOCK]" if o.is_mock else ""
        lines.append(f"\n[{o.status}]{tag} {o.label} — score {s.total}/100, confidenza {o.confidence}")
        lines.append(f"  post {s.frequency} · fonti {s.source_count} · crescita {growth} · "
                     f"intensità {s.intensity:.2f} · intento acquisto {s.purchase_intent:.0%} · "
                     f"prodotto fisico {s.physical_solvability:.2f}")
        for e in o.evidence:
            lines.append(f"  - \"{e.excerpt}\" — {e.platform}, {e.date}, {e.url}")
    skipped = sum(1 for o in report.opportunities if o.status == SKIP)
    lines.append(f"\nCluster scartati (SKIP): {skipped}")
    return "\n".join(lines)
