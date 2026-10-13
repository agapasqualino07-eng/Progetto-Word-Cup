"""Clustering semplice: TF-IDF + coseno in puro Python, greedy single-pass deterministico.

Limite noto: IT ed EN non si fondono (niente traduzione); un problema visto in
due lingue appare come due cluster. Meglio due cluster che una fusione sbagliata.
"""

import math
from collections import Counter

from dropship.problems.models import ProblemCluster


def tfidf_vectors(token_lists):
    n = len(token_lists)
    df = Counter()
    for toks in token_lists:
        df.update(set(toks))
    vectors = []
    for toks in token_lists:
        tf = Counter(toks)
        vec = {t: (c / len(toks)) * (math.log((1 + n) / (1 + df[t])) + 1.0) for t, c in tf.items()} if toks else {}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        vectors.append({t: v / norm for t, v in vec.items()})
    return vectors


def cosine(a, b):
    if len(a) > len(b):
        a, b = b, a
    return sum(v * b.get(t, 0.0) for t, v in a.items())


def _normalize(vec):
    norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return {t: v / norm for t, v in vec.items()}


def cluster_mentions(mentions, similarity=0.2, top_keywords=5):
    """Assegna ogni menzione al cluster col centroide più simile (>= soglia), altrimenti ne apre uno."""
    if not mentions:
        return []
    vectors = tfidf_vectors([m.tokens for m in mentions])
    clusters, sums = [], []
    for mention, vec in zip(mentions, vectors):
        best, best_sim = None, 0.0
        for idx, s in enumerate(sums):
            sim = cosine(vec, _normalize(s))
            if sim > best_sim:
                best, best_sim = idx, sim
        if best is not None and best_sim >= similarity:
            clusters[best].mentions.append(mention)
            for t, v in vec.items():
                sums[best][t] = sums[best].get(t, 0.0) + v
        else:
            clusters.append(ProblemCluster(cluster_id=len(clusters), mentions=[mention]))
            sums.append(dict(vec))
    for cl, s in zip(clusters, sums):
        # parole chiave: peso TF-IDF cumulato, a parità ordine alfabetico (deterministico)
        cl.keywords = tuple(t for t, _ in sorted(s.items(), key=lambda kv: (-kv[1], kv[0]))[:top_keywords])
    return clusters
