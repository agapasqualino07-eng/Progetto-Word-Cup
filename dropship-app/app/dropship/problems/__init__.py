"""Problem mining: dalle discussioni pubbliche ai problemi risolvibili con un prodotto fisico.

Solo fonti lecite (API ufficiali / RSS), nessun dato personale, evidenze sempre
citate (fonte, URL, data). Vedi docs/06-fonti-problemi.md.
"""

from dropship.problems.pipeline import MiningReport, format_report, mine_problems
from dropship.problems.scoring import ProblemThresholds, load_problem_thresholds
from dropship.problems.sources import (
    DiscussionSource,
    HackerNewsSource,
    MockDiscussionSource,
    RedditSource,
    RssSource,
    StackExchangeSource,
    YouTubeCommentsSource,
    build_discussion_sources,
    describe_discussion_sources,
)

__all__ = [
    "DiscussionSource", "MockDiscussionSource", "RedditSource", "StackExchangeSource",
    "YouTubeCommentsSource", "HackerNewsSource", "RssSource", "build_discussion_sources",
    "describe_discussion_sources", "mine_problems", "format_report", "MiningReport",
    "ProblemThresholds", "load_problem_thresholds",
]
