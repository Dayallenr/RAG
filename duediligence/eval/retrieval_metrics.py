"""
Retrieval metrics: recall@k, MRR, and nDCG@k.

Written out rather than pulled from a library so the exact definition
behind every number this project reports is inspectable — the same reason
the extraction eval spells out its tolerance. Several of these metrics have
more than one convention in common use, and the choices made here are
stated explicitly:

* **recall@k** is ``|relevant ∩ retrieved@k| / |relevant|`` — the fraction
  of known-relevant chunks that made the top k. Note this is *not* "did we
  get at least one hit", which is hit-rate@k (reported separately, since for
  a RAG system that can answer from a single good chunk it's often the more
  honest headline).

* **MRR** uses the reciprocal rank of the *first* relevant result, averaged
  over queries. A query with no relevant result in the top k contributes 0,
  rather than being dropped — dropping them inflates the score by silently
  evaluating only the queries that worked.

* **nDCG@k** uses binary relevance with the standard ``1/log2(rank+1)``
  discount. The ideal DCG is computed over ``min(|relevant|, k)`` results,
  so a query with more relevant chunks than k can still score 1.0 instead of
  being capped below it by an unreachable ideal.

All functions take ``retrieved`` as a ranked list of chunk_ids (best first)
and ``relevant`` as the set of ground-truth ids for that query.
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

__all__ = [
    "aggregate_metrics",
    "average_precision",
    "hit_rate_at_k",
    "ndcg_at_k",
    "recall_at_k",
    "reciprocal_rank",
]


def recall_at_k(retrieved: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """Fraction of relevant chunks appearing in the top k."""
    relevant = set(relevant)
    if not relevant:
        return 0.0
    found = sum(1 for chunk_id in retrieved[:k] if chunk_id in relevant)
    return found / len(relevant)


def hit_rate_at_k(retrieved: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """1.0 if any relevant chunk is in the top k, else 0.0."""
    relevant = set(relevant)
    return 1.0 if any(chunk_id in relevant for chunk_id in retrieved[:k]) else 0.0


def reciprocal_rank(retrieved: Sequence[str], relevant: Iterable[str]) -> float:
    """1/rank of the first relevant result (rank is 1-based); 0 if none."""
    relevant = set(relevant)
    for position, chunk_id in enumerate(retrieved, start=1):
        if chunk_id in relevant:
            return 1.0 / position
    return 0.0


def average_precision(retrieved: Sequence[str], relevant: Iterable[str]) -> float:
    """Mean of the precision values at each rank where a relevant result
    appears — the per-query term behind MAP. Divided by ``|relevant|`` (not
    by the number found), so failing to retrieve a relevant chunk at all
    costs score rather than being ignored."""
    relevant = set(relevant)
    if not relevant:
        return 0.0
    hits = 0
    precision_sum = 0.0
    for position, chunk_id in enumerate(retrieved, start=1):
        if chunk_id in relevant:
            hits += 1
            precision_sum += hits / position
    return precision_sum / len(relevant)


def ndcg_at_k(retrieved: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """Normalized discounted cumulative gain at k, binary relevance."""
    relevant = set(relevant)
    if not relevant:
        return 0.0

    dcg = sum(
        1.0 / math.log2(position + 1)
        for position, chunk_id in enumerate(retrieved[:k], start=1)
        if chunk_id in relevant
    )
    # Ideal ranking: every relevant chunk packed into the top positions,
    # capped at k because no ranking can surface more than k results.
    ideal_dcg = sum(1.0 / math.log2(position + 1) for position in range(1, min(len(relevant), k) + 1))
    return dcg / ideal_dcg if ideal_dcg else 0.0


def aggregate_metrics(
    per_query: list[tuple[Sequence[str], Iterable[str]]],
    k_values: Sequence[int] = (1, 3, 5, 10, 20),
) -> dict[str, float]:
    """Average every metric over a list of (retrieved, relevant) pairs.

    Queries whose ground truth is empty are skipped — they can't be scored
    either way, and counting them as zeros would understate the system.
    """
    scored = [(retrieved, set(relevant)) for retrieved, relevant in per_query]
    scored = [(retrieved, relevant) for retrieved, relevant in scored if relevant]
    if not scored:
        return {}

    metrics: dict[str, float] = {"queries": float(len(scored))}
    for k in k_values:
        metrics[f"recall@{k}"] = sum(recall_at_k(r, g, k) for r, g in scored) / len(scored)
        metrics[f"hit_rate@{k}"] = sum(hit_rate_at_k(r, g, k) for r, g in scored) / len(scored)
        metrics[f"ndcg@{k}"] = sum(ndcg_at_k(r, g, k) for r, g in scored) / len(scored)
    metrics["mrr"] = sum(reciprocal_rank(r, g) for r, g in scored) / len(scored)
    metrics["map"] = sum(average_precision(r, g) for r, g in scored) / len(scored)
    return metrics
