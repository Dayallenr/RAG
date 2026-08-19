"""
Hybrid retrieval: fuse the BM25 and dense rankings into one.

The Phase 4 baseline is the reason this exists and the reason it takes this
particular form. Measured on the 101-question eval set, BM25 beat dense
roughly 2x overall (recall@10 0.604 vs 0.322) — but not everywhere, and not
by subsuming it: BM25 won 41 queries the dense retriever missed, and the
dense retriever won 4 that BM25 missed. Two retrievers with genuinely
different failure modes and complementary wins is exactly the situation
fusion is for.

**Why Reciprocal Rank Fusion and not score normalization.** BM25 scores are
unbounded and corpus-dependent (a score of 7.8 means nothing on its own);
cosine similarities live in [-1, 1]. Combining them numerically requires
inventing a normalization — min-max over the returned window is the usual
choice, and it is unstable, because the scale then depends on which
documents happened to come back. RRF ignores scores entirely and fuses on
*rank*, which is the only quantity the two retrievers report on a common
scale. It has one parameter, it is deterministic, and it can be unit-tested
against hand-computed values.

    RRF(d) = sum over retrievers of 1 / (k + rank(d))

``k`` (default 60, the value from the original RRF paper) damps the
influence of the very top ranks so that one retriever ranking a document
first cannot alone dominate a document both retrievers rank highly.

**Candidate depth matters more than it looks.** Fusion can only consider
documents that at least one retriever returned, so retrieving only the top
10 from each and fusing to 10 mostly reproduces the individual rankings.
Each retriever is asked for ``candidate_k`` (default 50) and the fused list
is truncated afterwards.

OpenSearch 2.x also ships a native hybrid query (a search pipeline with a
normalization processor). This is deliberately client-side instead: the
fusion is then plain, inspectable Python that the eval harness can test
directly, and it stays identical across the local and AWS backends rather
than depending on a pipeline being registered on each cluster.
"""
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from opensearchpy import OpenSearch

from duediligence.index.opensearch_client import bm25_search, knn_search
from duediligence.tracing import span

logger = logging.getLogger(__name__)

__all__ = [
    "DEFAULT_DENSE_WEIGHT",
    "DEFAULT_RRF_K",
    "hybrid_search",
    "reciprocal_rank_fusion",
]

# From the original RRF paper (Cormack et al., 2009).
DEFAULT_RRF_K = 60

# Dense retrieval contributes at quarter weight, not equally.
#
# Chosen by the sweep in scripts/run_ablations.py (ablation A), which found
# equal weighting actively harmful on this corpus: at weight 1.0 the fusion
# scored *below* BM25 alone on recall@1 (0.183 vs 0.282), MRR, and nDCG,
# because the dense retriever is much weaker here (recall@10 0.322 vs 0.604)
# and equal weighting lets its weak candidates into the top ranks. Weight
# 0.25 keeps the deep-recall benefit — recall@10 0.663, the best of any
# weight tried and above BM25's 0.604 — which is what matters when the
# fused list is a candidate pool feeding a reranker.
#
# Caveat, since it changes how much to trust this: the weight was selected
# on the same 101-question eval set it is scored against, so that recall@10
# figure is optimistically biased. With one parameter and five values the
# bias is small, but it is not zero, and a held-out set would be the honest
# way to quote it.
DEFAULT_DENSE_WEIGHT = 0.25

# Ablation C: reranking recall@10 peaks at 50 candidates (0.713) and gets
# *worse* at 100 (0.703) while costing 70% more latency — a deeper pool
# gives the cross-encoder more chances to promote a distractor.
_DEFAULT_CANDIDATE_K = 50


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[str]],
    *,
    k: int = DEFAULT_RRF_K,
    weights: Sequence[float] | None = None,
) -> list[tuple[str, float]]:
    """Fuse ranked id lists into one ranking of (chunk_id, fused_score).

    ``weights`` optionally scales each retriever's contribution — used by
    the ablation to show what unequal weighting does, not by the default
    path, which weights both retrievers equally.

    Ties are broken by chunk_id so the output is fully deterministic; an
    eval that silently reorders ties between runs is not reproducible.
    """
    if weights is None:
        weights = [1.0] * len(rankings)
    if len(weights) != len(rankings):
        raise ValueError(f"got {len(rankings)} rankings but {len(weights)} weights")

    scores: dict[str, float] = {}
    for ranking, weight in zip(rankings, weights, strict=True):
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + weight / (k + rank)

    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


def hybrid_search(
    client: OpenSearch,
    index_name: str,
    query: str,
    query_vector: list[float],
    *,
    k: int = 10,
    candidate_k: int = _DEFAULT_CANDIDATE_K,
    rrf_k: int = DEFAULT_RRF_K,
    weights: Sequence[float] | None = None,
    filters: dict[str, Any] | None = None,
    ef_search: int | None = None,
) -> list[dict[str, Any]]:
    """Run both retrievers, fuse with RRF, return the top k hits.

    Hits carry the full chunk metadata (taken from whichever retriever
    returned the document) plus the fused ``score``, so callers downstream —
    the reranker, the API, the answer generator — see the same shape they
    get from the single-retriever functions.

    ``weights`` defaults to ``[1.0, DEFAULT_DENSE_WEIGHT]`` (lexical first,
    dense second) rather than equal weighting; see DEFAULT_DENSE_WEIGHT.

    ``ef_search`` is forwarded to the dense half only — it is an HNSW
    search-time parameter and has no lexical counterpart. It exists here so
    the ANN sweep (#14) can ask what a wider graph search is worth *through
    the pipeline this project serves*, not only on the dense path where a
    dense change shows up undamped.
    """
    if weights is None:
        weights = [1.0, DEFAULT_DENSE_WEIGHT]
    # Split spans: BM25 beats dense roughly 2x on this corpus, so which of
    # the two a slow query is waiting on is exactly the question a trace
    # should answer rather than leave to inference.
    with span("search.bm25", candidate_k=candidate_k):
        lexical = bm25_search(client, index_name, query, k=candidate_k, filters=filters)
    with span("search.knn", candidate_k=candidate_k):
        dense = knn_search(
            client,
            index_name,
            query_vector,
            k=candidate_k,
            filters=filters,
            ef_search=ef_search,
        )

    by_id: dict[str, dict[str, Any]] = {}
    for hit in (*lexical, *dense):
        by_id.setdefault(hit["chunk_id"], hit)

    fused = reciprocal_rank_fusion(
        [[h["chunk_id"] for h in lexical], [h["chunk_id"] for h in dense]],
        k=rrf_k,
        weights=weights,
    )

    results = []
    for chunk_id, score in fused[:k]:
        hit = dict(by_id[chunk_id])
        hit["score"] = score
        results.append(hit)
    return results
