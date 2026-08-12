"""
Cross-encoder reranking of retrieved candidates.

The retrievers in ``opensearch_client.py`` and ``hybrid_search.py`` are
*bi-encoders and lexical matchers*: they score a query against a document
representation computed without ever seeing the query. That is what makes
them fast enough to search 38k chunks. A cross-encoder instead runs the
query and the document through the model *together*, so it can weigh how
the specific question relates to the specific passage — much more accurate,
far too slow to run over a whole corpus.

The standard arrangement, and the one used here: retrieve a wide candidate
set cheaply (hybrid RRF over 50), then rerank only those with the expensive
model. Cost is bounded by the candidate count, not the corpus size.

**Memory note, learned the hard way on this machine.** This is an 8 GB Mac
that already swaps with OpenSearch's JVM and the embedding model resident
(see CLAUDE.md's embedding-throughput finding). ``ms-marco-MiniLM-L-6-v2``
is a small cross-encoder (~22M parameters) chosen for that reason, it is
loaded lazily so importing this module costs nothing, and scoring is
batched. Reranking 50 candidates is one forward pass over 50 pairs — the
per-query cost is real but bounded, and it is measured in the eval report
rather than assumed.
"""
from __future__ import annotations

import logging
from typing import Any

from duediligence.index.embed import resolve_device

logger = logging.getLogger(__name__)

__all__ = ["CrossEncoderReranker"]

_DEFAULT_BATCH_SIZE = 32


class CrossEncoderReranker:
    """Reorders retrieved hits by cross-encoder relevance score."""

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        *,
        device: str | None = None,
        batch_size: int = _DEFAULT_BATCH_SIZE,
    ) -> None:
        from sentence_transformers import CrossEncoder

        self.model_name = model_name
        self.device = resolve_device(device)
        self.batch_size = batch_size

        logger.info("loading reranker %s on %s", model_name, self.device)
        # max_length caps the query+passage pair; filing paragraphs run long
        # and the model's own limit is 512 tokens either way.
        self.model = CrossEncoder(model_name, device=self.device, max_length=512)

    def rerank(
        self, query: str, hits: list[dict[str, Any]], *, top_k: int | None = None
    ) -> list[dict[str, Any]]:
        """Return hits reordered by cross-encoder score, highest first.

        The original retrieval score is preserved as ``retrieval_score`` so
        a caller (or the ablation) can see how far the reranker moved a
        document rather than only seeing the final order.
        """
        if not hits:
            return []

        pairs = [(query, hit["text"]) for hit in hits]
        scores = self.model.predict(pairs, batch_size=self.batch_size, show_progress_bar=False)

        reranked = []
        for hit, score in zip(hits, scores, strict=True):
            updated = dict(hit)
            updated["retrieval_score"] = hit.get("score")
            updated["score"] = float(score)
            reranked.append(updated)

        # Tie-break on chunk_id so equal scores order deterministically —
        # an eval whose ties reshuffle between runs is not reproducible.
        reranked.sort(key=lambda h: (-h["score"], h["chunk_id"]))
        return reranked[:top_k] if top_k else reranked
