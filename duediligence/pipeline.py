"""
The end-to-end question-answering pipeline, assembled in one place.

Everything before this module is a component with its own tests; this is
the composition the API (Phase 8) serves and the groundedness eval (Phase 7)
measures, so that both exercise the *same* code path rather than each
re-wiring the parts slightly differently.

    question
      -> classify_query
      |
      +-- STRUCTURED: exact XBRL lookup. No model call. Returns a figure
      |   with the accession number that reported it. Falls through to the
      |   semantic path if the corpus has no such row, because "no data" is
      |   better delivered as retrieved prose than as a dead end.
      |
      +-- SEMANTIC: hybrid retrieval (RRF, dense at 0.25 weight)
                    -> cross-encoder rerank of 50 candidates
                    -> generate with enforced citations

Models are loaded once and held on the instance. The embedding model, the
cross-encoder, and an OpenSearch connection all cost real seconds to
construct, and on the 8 GB machine this project runs on, constructing them
per request is what makes the difference between a responsive API and one
that swaps (see CLAUDE.md's embedding-throughput finding).
"""
from __future__ import annotations

import logging
import time
from typing import Any

from duediligence.config import Config, load_config
from duediligence.generate.answer import GeneratedAnswer, generate_answer
from duediligence.generate.backends import TextGenerationBackend, default_generation_backend
from duediligence.index.embed import ChunkEmbedder
from duediligence.index.hybrid_search import hybrid_search
from duediligence.index.opensearch_client import build_client
from duediligence.route.query_router import Route, classify_query
from duediligence.route.structured_lookup import lookup_fact
from duediligence.tracing import span

logger = logging.getLogger(__name__)

__all__ = ["DueDiligencePipeline", "PipelineResult"]

_CANDIDATE_K = 50
_CONTEXT_PASSAGES = 6


class PipelineResult(dict):
    """A plain dict subclass so results serialize straight to JSON."""


class DueDiligencePipeline:
    def __init__(
        self,
        config: Config | None = None,
        *,
        enable_rerank: bool = True,
        enable_generation: bool = True,
        generation_backend: TextGenerationBackend | None = None,
    ) -> None:
        self.config = config or load_config()
        self.client = build_client(self.config.opensearch)
        self.index_name = self.config.opensearch.index_name
        self.embedder = ChunkEmbedder(self.config.models.embedding_model)
        self.enable_generation = enable_generation

        # Defaults to the hosted model so existing callers are unchanged.
        # Constructing it is free — the underlying client is built lazily —
        # so this does not require an API key to stand the pipeline up.
        self.generation_backend = generation_backend or default_generation_backend(self.config)

        self.reranker = None
        if enable_rerank:
            from duediligence.index.rerank import CrossEncoderReranker

            self.reranker = CrossEncoderReranker(self.config.models.reranker_model)

    def retrieve(
        self, question: str, *, k: int = _CONTEXT_PASSAGES, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Hybrid retrieval, then reranking if enabled."""
        with span("retrieve", k=k, reranked=self.reranker is not None) as retrieval:
            with span("embed.query", model=self.embedder.model_name):
                vector = self.embedder.embed_query(question)

            if self.reranker is None:
                hits = hybrid_search(
                    self.client, self.index_name, question, vector, k=k,
                    candidate_k=_CANDIDATE_K, filters=filters,
                )
                retrieval.set_attribute("hits", len(hits))
                return hits

            candidates = hybrid_search(
                self.client, self.index_name, question, vector,
                k=_CANDIDATE_K, candidate_k=_CANDIDATE_K, filters=filters,
            )
            # Recorded because rerank cost scales with this, and the
            # ablation already found depth 100 *worse* than 50 at 70% more
            # latency — a trace should show which depth actually ran.
            with span("rerank", candidates=len(candidates), top_k=k):
                hits = self.reranker.rerank(question, candidates, top_k=k)
            retrieval.set_attribute("hits", len(hits))
            return hits

    def answer(
        self,
        question: str,
        *,
        k: int = _CONTEXT_PASSAGES,
        filters: dict[str, Any] | None = None,
    ) -> PipelineResult:
        started = time.perf_counter()

        with span("duediligence.answer", question_chars=len(question)) as root:
            with span("route.classify"):
                decision = classify_query(question)
            root.set_attribute("route", decision.route.value)

            if decision.route is Route.STRUCTURED:
                with span(
                    "route.structured_lookup",
                    concept=decision.concept,
                    company=decision.company,
                    fiscal_year=decision.fiscal_year,
                ) as lookup:
                    fact = lookup_fact(
                        decision.concept, decision.company, decision.fiscal_year
                    )
                    lookup.set_attribute("found", fact is not None)
                if fact is not None:
                    # No model call on this path at all, which a trace makes
                    # obvious: a structured answer has no generate span.
                    root.set_attribute("answered_by", "structured")
                    return PipelineResult(
                        question=question,
                        route="structured",
                        routing_reasons=decision.reasons,
                        answer=(
                            f"{fact.company} {decision.concept} for fiscal year "
                            f"{fact.fiscal_year} was {fact.formatted_value()}."
                        ),
                        structured_fact=fact.to_dict(),
                        citations=[{
                            "accession_number": fact.accession_number,
                            "source_url": fact.source_url,
                            "company": fact.company,
                        }],
                        passages=[],
                        refused=False,
                        latency_ms=round((time.perf_counter() - started) * 1000, 1),
                    )
                # The corpus has no row for this key. Falling through to search
                # is better than reporting "no data": the figure may well be
                # stated in prose the retriever can find.
                logger.info(
                    "structured route found no fact for %s/%s/%s — falling back to semantic",
                    decision.company, decision.concept, decision.fiscal_year,
                )
                decision.reasons.append("no matching XBRL fact — fell back to semantic search")

            passages = self.retrieve(question, k=k, filters=filters)

            generated: GeneratedAnswer | None = None
            if self.enable_generation:
                with span(
                    "generate",
                    backend=self.generation_backend.name,
                    model=self.generation_backend.model,
                    passages=len(passages),
                ) as generation:
                    generated = generate_answer(
                        question, passages,
                        backend=self.generation_backend,
                        max_passages=k,
                    )
                    generation.set_attribute("refused", generated.refused)
                    generation.set_attribute("citations", len(generated.citations))

            root.set_attribute("answered_by", "semantic")

            return PipelineResult(
                question=question,
                route="semantic",
                routing_reasons=decision.reasons,
                answer=generated.answer if generated else None,
                structured_fact=None,
                citations=generated.citations if generated else [],
                passages=[
                    {
                        "chunk_id": p.get("chunk_id"),
                        "company": p.get("company"),
                        "filing_type": p.get("filing_type"),
                        "filing_date": p.get("filing_date"),
                        "section": p.get("section"),
                        "source_url": p.get("source_url"),
                        "score": p.get("score"),
                        "text": p.get("text"),
                    }
                    for p in passages
                ],
                refused=generated.refused if generated else False,
                latency_ms=round((time.perf_counter() - started) * 1000, 1),
            )
