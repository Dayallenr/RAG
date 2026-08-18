"""
Prometheus metrics for the serving layer.

Kept in its own module so the metric objects are defined exactly once.
``prometheus_client`` registers metrics globally by name, and defining a
Counter twice — which happens easily if metrics live in a module that gets
imported under two names, or re-imported by a test — raises a duplicate
registration error at import time.

The chosen metrics answer the questions this system would actually be
debugged with:

* ``duediligence_requests_total`` — traffic and error rate per endpoint.
* ``duediligence_request_latency_seconds`` — end-to-end latency histogram.
* ``duediligence_retrieval_latency_seconds`` — retrieval alone, so a
  slowdown can be attributed to search versus generation without guessing.
  This project has already been bitten once by attributing a slowdown to the
  wrong component (see the MPS/CPU-time entry in
  docs/engineering-notes.md), which is the reason this is split out rather
  than folded into the request timer.
* ``duediligence_route_total`` — structured vs semantic split, which is the
  headline behavioural claim of the router and should be observable in
  production, not just in an eval.

Histogram buckets are set for this system's real latencies, measured rather
than guessed: structured lookups return in single-digit milliseconds,
retrieval with reranking around 350 ms, and generation adds seconds.
"""
from __future__ import annotations

from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

__all__ = [
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "RETRIEVAL_LATENCY",
    "ROUTE_COUNT",
    "metrics_response",
]

REQUEST_COUNT = Counter(
    "duediligence_requests_total",
    "API requests by endpoint and outcome",
    ["endpoint", "status"],
)

# Buckets span 5 ms (a structured lookup) to 10 s (generation), because the
# default prometheus buckets top out at 10s but are too coarse below 100ms
# to show the structured route's latency at all.
_LATENCY_BUCKETS = (0.005, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

REQUEST_LATENCY = Histogram(
    "duediligence_request_latency_seconds",
    "End-to-end request latency",
    ["endpoint"],
    buckets=_LATENCY_BUCKETS,
)

RETRIEVAL_LATENCY = Histogram(
    "duediligence_retrieval_latency_seconds",
    "Retrieval latency, excluding generation",
    buckets=_LATENCY_BUCKETS,
)

ROUTE_COUNT = Counter(
    "duediligence_route_total",
    "Queries by routing decision",
    ["route"],
)


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
