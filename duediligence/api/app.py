"""
FastAPI serving layer.

**Models load once, at startup, not per request.** The embedding model, the
cross-encoder, and the OpenSearch connection each cost real seconds to
construct; building them per request would also mean holding several copies
resident, which on the 8 GB machine this runs on is the difference between
responsive and swapping (see docs/engineering-notes.md). The pipeline is
therefore built in the lifespan handler and shared.

**Readiness and liveness are different checks, deliberately.** ``/healthz``
answers "is this process alive" — it must not touch OpenSearch, or a
transient search-cluster blip would get the pod killed and restarted, which
fixes nothing and drops in-flight requests. ``/readyz`` answers "can this
process actually serve traffic", which does require OpenSearch, and failing
it removes the pod from the load balancer without restarting it. Kubernetes
maps these to livenessProbe and readinessProbe respectively (see k8s/).

**Generation is optional at runtime.** ``ENABLE_GENERATION=false`` serves
retrieval and structured lookup without ever calling Gemini — which is what
makes the API demoable, and CI-testable, against a 20-requests/day quota.
"""
from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from duediligence.api.metrics import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    RETRIEVAL_LATENCY,
    ROUTE_COUNT,
    metrics_response,
)
from duediligence.tracing import configure_tracing

logger = logging.getLogger(__name__)

__all__ = ["app", "create_app"]

_MAX_QUESTION_CHARS = 1000


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=_MAX_QUESTION_CHARS)
    k: int = Field(6, ge=1, le=20, description="passages to retrieve and cite")
    company: str | None = Field(None, description="restrict to one ticker, e.g. COLB")
    filing_type: str | None = Field(None, description="restrict to one form, e.g. 10-K")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=_MAX_QUESTION_CHARS)
    k: int = Field(10, ge=1, le=50)
    company: str | None = None
    filing_type: str | None = None


def _filters(company: str | None, filing_type: str | None) -> dict[str, Any] | None:
    filters = {}
    if company:
        filters["company"] = company.upper()
    if filing_type:
        filters["filing_type"] = filing_type
    return filters or None


@asynccontextmanager
async def lifespan(app: FastAPI):
    from duediligence.pipeline import DueDiligencePipeline

    enable_generation = os.environ.get("ENABLE_GENERATION", "true").lower() != "false"
    enable_rerank = os.environ.get("ENABLE_RERANK", "true").lower() != "false"

    logger.info(
        "loading pipeline (generation=%s, rerank=%s)", enable_generation, enable_rerank
    )
    started = time.perf_counter()
    app.state.pipeline = DueDiligencePipeline(
        enable_rerank=enable_rerank, enable_generation=enable_generation
    )
    logger.info("pipeline ready in %.1fs", time.perf_counter() - started)
    yield
    app.state.pipeline = None


def get_pipeline(request: Request):
    pipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        # 503, not 500: the process is fine, it just is not ready to serve.
        raise HTTPException(status_code=503, detail="pipeline is not loaded")
    return pipeline


# Annotated form rather than a Depends() default: a function call in an
# argument default is evaluated once at import and flagged by linters (B008).
PipelineDep = Annotated[Any, Depends(get_pipeline)]


def _served_identity(request: Request) -> dict[str, Any]:
    """What this process is actually serving with: model, index, profile, backend.

    An embedding model and its index are a matched pair, and a container
    holding the wrong one fails silently — cosine similarity across two
    incompatible vector spaces returns a number, so the answers look
    ordinary and every one of them is built on nothing. Nothing in the
    request path can detect that. Reporting the pair on the health
    endpoints is what turns it from an invisible failure into an
    observable one.

    Never raises. Liveness must answer before the pipeline finishes
    loading, so an absent pipeline reports nulls rather than an error —
    with the same four keys, so a caller parsing this never has to branch
    on whether the field it wants is present.
    """
    pipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        return {"model": None, "index": None, "profile": None, "backend": None}
    return {
        "model": pipeline.model_name,
        "index": pipeline.index_name,
        "profile": pipeline.profile,
        "backend": pipeline.backend,
    }


def create_app() -> FastAPI:
    # Installed once at startup. A no-op unless OTEL_EXPORTER_OTLP_ENDPOINT
    # is set, so the default deployment carries no exporter and no
    # background threads — see duediligence/tracing.py.
    configure_tracing()

    app = FastAPI(
        title="Bank M&A Due-Diligence RAG",
        description=(
            "Question answering over real SEC EDGAR filings from five US regional banks, "
            "centered on the 2023 Columbia Banking System / Umpqua Holdings merger of equals. "
            "Factual queries route to exact XBRL lookup; narrative queries route to hybrid "
            "search with cross-encoder reranking and cited generation."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/healthz", tags=["ops"])
    def healthz(request: Request) -> dict[str, Any]:
        """Liveness: is the process up. Deliberately does not touch OpenSearch —
        a search outage must not cause pod restarts.

        It does report the loaded model, which costs nothing: the name is an
        attribute already in memory. Liveness is the endpoint still answering
        while readiness fails, which is exactly when "what is this container
        actually holding" is the question being asked.
        """
        return {"status": "ok", **_served_identity(request)}

    @app.get("/readyz", tags=["ops"])
    def readyz(request: Request) -> dict[str, Any]:
        """Readiness: can this process actually serve. Requires the pipeline
        to be loaded and the index to be reachable."""
        pipeline = getattr(request.app.state, "pipeline", None)
        if pipeline is None:
            raise HTTPException(status_code=503, detail="pipeline not loaded")
        try:
            reachable = pipeline.client.indices.exists(index=pipeline.index_name)
        except Exception as error:  # noqa: BLE001 - any failure means not ready
            raise HTTPException(status_code=503, detail=f"opensearch unreachable: {error}") from error
        if not reachable:
            raise HTTPException(status_code=503, detail=f"index {pipeline.index_name} missing")
        # Model and index reported together, because the failure worth
        # catching is the pair being mismatched — see _served_identity.
        return {"status": "ready", **_served_identity(request)}

    @app.get("/metrics", tags=["ops"])
    def metrics():
        return metrics_response()

    @app.post("/ask", tags=["qa"])
    def ask(payload: AskRequest, pipeline: PipelineDep) -> dict[str, Any]:
        """Answer a question, routing to exact lookup or cited generation."""
        started = time.perf_counter()
        try:
            result = pipeline.answer(
                payload.question, k=payload.k,
                filters=_filters(payload.company, payload.filing_type),
            )
        except Exception as error:  # noqa: BLE001 - surface as 500 with a clean message
            REQUEST_COUNT.labels(endpoint="/ask", status="error").inc()
            logger.exception("ask failed")
            raise HTTPException(status_code=500, detail=str(error)) from error

        REQUEST_COUNT.labels(endpoint="/ask", status="ok").inc()
        REQUEST_LATENCY.labels(endpoint="/ask").observe(time.perf_counter() - started)
        ROUTE_COUNT.labels(route=result["route"]).inc()
        return result

    @app.post("/search", tags=["qa"])
    def search(payload: SearchRequest, pipeline: PipelineDep) -> dict[str, Any]:
        """Retrieval only — no generation, no Gemini quota spent."""
        started = time.perf_counter()
        try:
            hits = pipeline.retrieve(
                payload.query, k=payload.k,
                filters=_filters(payload.company, payload.filing_type),
            )
        except Exception as error:  # noqa: BLE001
            REQUEST_COUNT.labels(endpoint="/search", status="error").inc()
            logger.exception("search failed")
            raise HTTPException(status_code=500, detail=str(error)) from error

        elapsed = time.perf_counter() - started
        REQUEST_COUNT.labels(endpoint="/search", status="ok").inc()
        REQUEST_LATENCY.labels(endpoint="/search").observe(elapsed)
        RETRIEVAL_LATENCY.observe(elapsed)
        return {
            "query": payload.query,
            "count": len(hits),
            "results": [
                {
                    "chunk_id": h.get("chunk_id"),
                    "score": h.get("score"),
                    "company": h.get("company"),
                    "filing_type": h.get("filing_type"),
                    "filing_date": h.get("filing_date"),
                    "section": h.get("section"),
                    "chunk_type": h.get("chunk_type"),
                    "source_url": h.get("source_url"),
                    "text": h.get("text"),
                }
                for h in hits
            ],
        }

    @app.get("/route", tags=["qa"])
    def route(question: str) -> dict[str, Any]:
        """Expose the routing decision and its reasoning without running it.

        The router is a deterministic rule set, not an LLM — this endpoint
        exists so that claim is inspectable rather than asserted.
        """
        from duediligence.route.query_router import classify_query

        decision = classify_query(question)
        return {
            "question": question,
            "route": decision.route.value,
            "concept": decision.concept,
            "company": decision.company,
            "fiscal_year": decision.fiscal_year,
            "reasons": decision.reasons,
        }

    return app


app = create_app()
