"""Modelli del problem-mining (dataclass, nessuna dipendenza esterna).

Privacy by design: ``Post`` NON ha un campo autore. Gli adapter non leggono
username, avatar, ID utente: nel modello semplicemente non c'è posto.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Tuple

from dropship.models import MISSING, MOCK

MAX_POST_CHARS = 1500  # testo minimo necessario: il resto viene troncato
MAX_EXCERPT_CHARS = 200


@dataclass(frozen=True)
class Post:
    """Un contenuto pubblico (domanda, commento, thread) già ripulito.

    - ``source``: "MOCK" per dati dimostrativi, altrimenti il nome della fonte
      reale (es. "REDDIT"). Mai un dato MOCK con source reale.
    - ``platform``: community/sito (es. "reddit:r/italy", "stackexchange:diy").
      È l'unità usata per contare le fonti *indipendenti*.
    - ``created_at``: datetime UTC o None (= DATO MANCANTE, mai stimata).
    """

    source: str
    platform: str
    url: str
    text: str
    created_at: Optional[datetime] = None
    lang: str = ""
    retention_days: Optional[int] = None  # obbligo di cancellazione della fonte (ToS)

    @property
    def is_mock(self):
        return self.source == MOCK


@dataclass(frozen=True)
class ProblemMention:
    """Una frase che esprime un problema, estratta da un Post."""

    post: Post
    sentence: str  # frase normalizzata e già redatta (niente email/@utente/telefoni)
    patterns: Tuple[str, ...]
    intensity: float  # 0..1 (emozione/urgenza)
    purchase_intent: bool
    physical: float  # 0..1 risolvibilità con un prodotto fisico spedibile (euristica lessicale)
    tokens: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Evidence:
    """Citazione di evidenza: SEMPRE derivata da un Post realmente ricevuto."""

    source: str
    platform: str
    url: str
    date: str  # ISO yyyy-mm-dd oppure "DATO MANCANTE"
    excerpt: str
    retain_until: Optional[str] = None  # ISO; oltre questa data va cancellata

    @staticmethod
    def from_mention(mention, collected_at):
        """``collected_at``: quando abbiamo raccolto il dato (il termine di
        conservazione imposto dalla fonte decorre da lì, non dalla data del post)."""
        post = mention.post
        date = post.created_at.date().isoformat() if post.created_at else MISSING
        retain = None
        if post.retention_days is not None:
            retain = (collected_at + timedelta(days=post.retention_days)).date().isoformat()
        excerpt = mention.sentence
        if len(excerpt) > MAX_EXCERPT_CHARS:
            excerpt = excerpt[: MAX_EXCERPT_CHARS - 1].rstrip() + "…"
        return Evidence(post.source, post.platform, post.url, date, excerpt, retain)


@dataclass(frozen=True)
class ProblemScore:
    frequency: int  # menzioni uniche
    growth: Optional[float]  # (ultimi N gg - N gg precedenti) / max(precedenti,1); None se date mancanti
    intensity: float
    purchase_intent: float
    physical_solvability: float
    source_count: int  # piattaforme indipendenti
    total: float  # 0..100


@dataclass
class ProblemCluster:
    cluster_id: int
    mentions: list = field(default_factory=list)
    keywords: Tuple[str, ...] = ()

    @property
    def label(self):
        return " / ".join(self.keywords[:3]) if self.keywords else MISSING


@dataclass(frozen=True)
class Opportunity:
    label: str
    keywords: Tuple[str, ...]
    status: str  # OPPORTUNITA | DA MONITORARE | SKIP
    confidence: str  # ALTA | MEDIA | BASSA | INSUFFICIENTE
    score: ProblemScore
    reasons: Tuple[str, ...]
    evidence: Tuple[Evidence, ...]
    source: str  # "MOCK" se anche una sola evidenza è MOCK

    @property
    def is_mock(self):
        return self.source == MOCK
