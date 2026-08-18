# 0004 — REST serving layer rather than RPC

**Status:** accepted

## Context

The retrieval pipeline needs to be served over a network: `/ask`, `/search`,
`/route`, plus health, readiness and metrics endpoints. gRPC is the
conventional choice for an internal ML service — binary protobuf, generated
clients, streaming, and materially lower per-call overhead.

## Decision

FastAPI over HTTP/JSON.

## Alternatives considered

- **gRPC.** The stronger choice on raw merit for a service-to-service ML
  endpoint. Rejected on two grounds. First, the callers here are a browser,
  `curl`, and a load-testing tool — for all three, JSON over HTTP is
  directly inspectable and protobuf is not, and the ability to paste a
  request into a terminal and read the answer has been worth more during
  development than the latency saving. Second, the numbers say serialization
  is not where the time goes: in `results/retrieval/report.json` the hybrid
  path averages 359 ms and hybrid-plus-rerank 905 ms, so the cross-encoder
  alone costs roughly 546 ms per query. Protobuf would save single-digit
  milliseconds against that. Optimising a fraction of a percent while a
  model forward pass owns the rest is the wrong end of the problem.
- **A plain ASGI app without FastAPI.** Rejected: Pydantic request/response
  models and the generated OpenAPI schema are most of why this endpoint is
  documented at all.

## Consequences

**Accepted downside.** JSON serialization and HTTP/1.1 framing cost more per
call than protobuf over HTTP/2, and there is no generated typed client for
consumers in other languages. If this ever became a high-QPS internal
dependency, that would need revisiting.

**Honest secondary reason.** I have another portfolio project built on gRPC.
Choosing REST here means the two read as two systems with different
constraints rather than one pattern applied twice. That is a presentation
motive, not an engineering one, and it is recorded as such — but the
engineering case above stands on its own and came first.

**Benefit.** `/metrics` in Prometheus text format, OpenAPI docs at `/docs`,
and Kubernetes probes that hit ordinary HTTP endpoints all come free rather
than needing a gRPC-specific health protocol and an exporter sidecar.
