"""ProblemScore per cluster e decisione OPPORTUNITA / DA MONITORARE / SKIP.

Pesi (somma 100): frequenza 25, intento d'acquisto 20, risolvibilità fisica 15,
intensità 15, crescita 15, varietà di fonti 10. Un problema visto su UNA sola
piattaforma vale meno (moltiplicatore ``single_source_penalty``). Sotto il numero
minimo di evidenze -> SKIP, senza calcolare nulla di "promettente".
"""

import math
from dataclasses import dataclass
from datetime import timedelta

from dropship.config import ConfigError
from dropship.models import MOCK
from dropship.problems.models import Evidence, Opportunity, ProblemScore

OPPORTUNITY = "OPPORTUNITA"
WATCH = "DA MONITORARE"
SKIP = "SKIP"

WEIGHTS = {"frequency": 25, "purchase_intent": 20, "physical": 15, "intensity": 15, "growth": 15,
           "diversity": 10}


@dataclass(frozen=True)
class ProblemThresholds:
    min_evidence: int = 5  # post unici minimi: sotto -> SKIP (skill customer-research: >= 5)
    min_sources: int = 2  # piattaforme indipendenti minime per OPPORTUNITA
    min_score: float = 55.0  # 0..100
    min_physical: float = 0.4  # sotto: non risolvibile con un prodotto spedibile -> SKIP
    cluster_similarity: float = 0.2
    growth_window_days: int = 30
    frequency_saturation: int = 20  # oltre N menzioni la frequenza non aggiunge punti
    single_source_penalty: float = 0.7
    max_evidence: int = 5  # citazioni mostrate per opportunità


def _num(env, name, default, kind):
    raw = env.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        return kind(str(raw).strip())
    except ValueError:
        raise ConfigError(f"{name}: valore non numerico") from None


def load_problem_thresholds(env):
    th = ProblemThresholds(
        min_evidence=_num(env, "DROPSHIP_PROBLEM_MIN_EVIDENCE", 5, int),
        min_sources=_num(env, "DROPSHIP_PROBLEM_MIN_SOURCES", 2, int),
        min_score=_num(env, "DROPSHIP_PROBLEM_MIN_SCORE", 55.0, float),
        min_physical=_num(env, "DROPSHIP_PROBLEM_MIN_PHYSICAL", 0.4, float),
        cluster_similarity=_num(env, "DROPSHIP_PROBLEM_CLUSTER_SIMILARITY", 0.2, float),
        growth_window_days=_num(env, "DROPSHIP_PROBLEM_GROWTH_WINDOW_DAYS", 30, int),
    )
    if th.min_evidence < 2:
        raise ConfigError("DROPSHIP_PROBLEM_MIN_EVIDENCE: almeno 2 (una sola citazione non è un pattern)")
    if th.min_sources < 1:
        raise ConfigError("DROPSHIP_PROBLEM_MIN_SOURCES: deve essere >= 1")
    if not 0 <= th.min_score <= 100:
        raise ConfigError("DROPSHIP_PROBLEM_MIN_SCORE: deve essere tra 0 e 100")
    for name, v in (("DROPSHIP_PROBLEM_MIN_PHYSICAL", th.min_physical),
                    ("DROPSHIP_PROBLEM_CLUSTER_SIMILARITY", th.cluster_similarity)):
        if not 0 < v <= 1:
            raise ConfigError(f"{name}: deve essere in (0, 1]")
    if th.growth_window_days < 1:
        raise ConfigError("DROPSHIP_PROBLEM_GROWTH_WINDOW_DAYS: deve essere >= 1")
    return th


def growth_rate(mentions, now, window_days):
    """(post ultimi N gg - post N gg precedenti) / max(precedenti, 1). None se nessuna data."""
    dated = list({m.post.url: m.post.created_at for m in mentions if m.post.created_at is not None}.values())
    if not dated:
        return None
    w = timedelta(days=window_days)
    recent = sum(1 for d in dated if now - w <= d <= now)
    previous = sum(1 for d in dated if now - 2 * w <= d < now - w)
    return (recent - previous) / max(previous, 1)


def _mean(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def score_cluster(cluster, now, th):
    ms = cluster.mentions
    n = len({m.post.url for m in ms})  # post unici: due frasi dello stesso post contano 1
    platforms = {m.post.platform for m in ms}
    growth = growth_rate(ms, now, th.growth_window_days)
    intensity = _mean(m.intensity for m in ms)
    intent = _mean(1.0 if m.purchase_intent else 0.0 for m in ms)
    physical = _mean(m.physical for m in ms)

    f_freq = min(1.0, math.log1p(n) / math.log1p(th.frequency_saturation))
    # crescita: -100% -> 0, stabile -> 0.5, raddoppio o più -> 1. Dato mancante -> 0 (mai stimato).
    f_growth = 0.0 if growth is None else max(0.0, min(1.0, (growth + 1.0) / 2.0))
    f_div = min(1.0, (len(platforms) - 1) / 2.0)
    total = (WEIGHTS["frequency"] * f_freq + WEIGHTS["purchase_intent"] * intent
             + WEIGHTS["physical"] * physical + WEIGHTS["intensity"] * intensity
             + WEIGHTS["growth"] * f_growth + WEIGHTS["diversity"] * f_div)
    if len(platforms) <= 1:
        total *= th.single_source_penalty
    return ProblemScore(
        frequency=n, growth=None if growth is None else round(growth, 3), intensity=round(intensity, 3),
        purchase_intent=round(intent, 3), physical_solvability=round(physical, 3),
        source_count=len(platforms), total=round(total, 1),
    )


def _confidence(score, th):
    if score.frequency < th.min_evidence:
        return "INSUFFICIENTE"
    if score.source_count >= 3:
        return "ALTA"
    if score.source_count == 2:
        return "MEDIA"
    return "BASSA"


def _pick_evidence(mentions, th, collected_at):
    """Citazioni reali: prima una per piattaforma (varietà), poi le più recenti."""
    ordered = sorted(mentions, key=lambda m: (m.post.created_at is None,
                                              -(m.post.created_at.timestamp() if m.post.created_at else 0)))
    picked, platforms, urls = [], set(), set()
    for m in ordered:  # 1) una per piattaforma
        if m.post.platform not in platforms:
            picked.append(m)
            platforms.add(m.post.platform)
            urls.add(m.post.url)
    for m in ordered:  # 2) poi post diversi
        if m.post.url not in urls:
            picked.append(m)
            urls.add(m.post.url)
    return tuple(Evidence.from_mention(m, collected_at) for m in picked[: th.max_evidence])


def evaluate_cluster(cluster, now, th):
    score = score_cluster(cluster, now, th)
    reasons = []
    if score.frequency < th.min_evidence:
        status = SKIP
        reasons.append(f"evidenze insufficienti: {score.frequency} < {th.min_evidence}")
    elif score.physical_solvability < th.min_physical:
        status = SKIP
        reasons.append(f"non risolvibile con prodotto fisico spedibile (euristica {score.physical_solvability:.2f}"
                       f" < {th.min_physical})")
    elif score.source_count < th.min_sources:
        status = WATCH
        reasons.append(f"una sola fonte ({score.source_count} < {th.min_sources}): da confermare altrove")
    elif score.total < th.min_score:
        status = WATCH
        reasons.append(f"punteggio {score.total} < {th.min_score}")
    else:
        status = OPPORTUNITY
        reasons.append(f"punteggio {score.total} >= {th.min_score} su {score.source_count} fonti")
    if score.growth is None:
        reasons.append("crescita: DATO MANCANTE (date assenti)")
    is_mock = any(m.post.is_mock for m in cluster.mentions)
    if is_mock:
        reasons.append("DATI MOCK: solo dimostrativi, non usare per decisioni")
    sources = {m.post.source for m in cluster.mentions}
    return Opportunity(
        label=cluster.label, keywords=cluster.keywords, status=status, confidence=_confidence(score, th),
        score=score, reasons=tuple(reasons), evidence=_pick_evidence(cluster.mentions, th, now),
        source=MOCK if is_mock else "+".join(sorted(sources)),
    )
