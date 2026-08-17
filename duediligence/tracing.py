"""
Distributed tracing for the question-answering path.

The metrics in ``api/metrics.py`` answer *how long a request took*. They
cannot answer *where the time went*, and this project has already been
burned once by guessing at that: a throughput collapse was attributed to
blocking on OpenSearch because ``ps`` showed 2.7% CPU, when the real cause
was MPS work running on the GPU — which does not register as process CPU
time at all (CLAUDE.md's embedding-throughput finding). A latency
breakdown is not a nice-to-have here; the absence of one has already
produced a wrong diagnosis.

The spans mirror the pipeline's real stages, so a trace reads as the
pipeline's own shape:

    duediligence.answer
      route.classify
      route.structured_lookup      (structured path only)
      retrieve
        embed.query
        search.hybrid
          search.bm25
          search.knn
        rerank
      generate

**Tracing never changes behaviour and never fails a request.** With no
endpoint configured, ``span()`` yields a no-op object and the process holds
no exporter, no background threads, and no queue. That is what lets the same
code run untraced on the 8 GB dev machine, traced against a local collector,
and traced into a cloud backend during the AWS window — by environment
variable alone, with nothing recompiled and no code path that only executes
in production.

Configuration is the OpenTelemetry standard ``OTEL_EXPORTER_OTLP_ENDPOINT``
rather than a bespoke variable, so pointing this at a managed backend later
needs no code change — which is the whole reason the export target is
configurable rather than hard-coded.
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["configure_tracing", "reset_tracing", "span", "tracing_enabled"]

SERVICE_NAME = "duediligence-api"

_OFF_VALUES = {"0", "off", "false", "no"}

_tracer: Any | None = None
_configured = False


class _NoOpSpan:
    """Stands in for a span when tracing is off.

    Accepts the same calls a real span does and discards them, so callers
    never branch on whether tracing is enabled — a conditional at every
    instrumentation site is how instrumentation rots.
    """

    def set_attribute(self, key: str, value: Any) -> None:  # noqa: D102
        pass

    def add_event(self, name: str, attributes: dict | None = None) -> None:  # noqa: D102
        pass

    def record_exception(self, exception: BaseException) -> None:  # noqa: D102
        pass


_NOOP_SPAN = _NoOpSpan()


def tracing_enabled() -> bool:
    """Tracing is on when an OTLP endpoint is configured and it is not
    explicitly switched off."""
    if os.environ.get("DUEDILIGENCE_TRACING", "").strip().lower() in _OFF_VALUES:
        return False
    return bool(os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"))


def configure_tracing(
    *,
    service_name: str = SERVICE_NAME,
    endpoint: str | None = None,
    tracer_provider: Any | None = None,
) -> bool:
    """Install a tracer provider. Returns whether tracing ended up enabled.

    Idempotent: calling it twice is a no-op, because the serving app calls it
    at startup and a test may call it too, and installing two providers
    silently drops the spans from one of them.

    ``tracer_provider`` is injectable so tests can supply an in-memory
    provider without an exporter, a collector, or a network.
    """
    global _tracer, _configured

    if _configured and tracer_provider is None:
        return _tracer is not None

    if tracer_provider is not None:
        _tracer = tracer_provider.get_tracer(__name__)
        _configured = True
        return True

    endpoint = endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint or not tracing_enabled():
        logger.info(
            "tracing off (set OTEL_EXPORTER_OTLP_ENDPOINT to enable); metrics unaffected"
        )
        _configured = True
        _tracer = None
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.warning(
            "OTEL_EXPORTER_OTLP_ENDPOINT is set but opentelemetry is not installed"
        )
        _configured = True
        _tracer = None
        return False

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")))
    trace.set_tracer_provider(provider)

    _tracer = provider.get_tracer(__name__)
    _configured = True
    logger.info("tracing enabled, exporting to %s as %s", endpoint, service_name)
    return True


def reset_tracing() -> None:
    """Drop the installed tracer. For tests, which need a clean slate
    between cases that install different providers."""
    global _tracer, _configured
    _tracer = None
    _configured = False


@contextmanager
def span(name: str, **attributes: Any):
    """Open a span, or yield a no-op when tracing is off.

    Attributes whose value is ``None`` are dropped rather than recorded as
    the string "None" — an absent filter and a filter of the literal text
    "None" are different facts, and only one of them is true.
    """
    if not _configured:
        configure_tracing()

    if _tracer is None:
        yield _NOOP_SPAN
        return

    with _tracer.start_as_current_span(name) as active:
        for key, value in attributes.items():
            if value is not None:
                active.set_attribute(key, value)
        yield active
