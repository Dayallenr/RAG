"""Tests for distributed tracing.

Spans are asserted against an in-memory exporter — no collector, no network,
no OTLP. The pipeline under test is built by assigning fake collaborators
rather than by running its constructor, which would load two transformer
models and need a live OpenSearch (the same reason `test_api.py` stubs it).

The property worth defending hardest is that tracing changes nothing: with
no endpoint configured there is no exporter, no background thread, and no
behavioural difference. Instrumentation that can alter a result is worse
than no instrumentation.
"""
from __future__ import annotations

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from duediligence.pipeline import DueDiligencePipeline, PipelineResult
from duediligence.tracing import configure_tracing, reset_tracing, span, tracing_enabled
from tests.fakes import FakeBackend


@pytest.fixture
def spans():
    """An in-memory tracer installed for the duration of one test."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    configure_tracing(tracer_provider=provider)
    yield exporter
    reset_tracing()


def names(exporter) -> list[str]:
    return [s.name for s in exporter.get_finished_spans()]


def by_name(exporter, name):
    return next(s for s in exporter.get_finished_spans() if s.name == name)


class FakeEmbedder:
    model_name = "bge-small-en-v1.5"

    def embed_query(self, question):
        return [0.0, 1.0]


class FakeReranker:
    def rerank(self, query, hits, *, top_k=None):
        return hits[:top_k] if top_k else hits


def _hit(chunk_id="c1"):
    return {
        "chunk_id": chunk_id, "score": 0.9, "company": "COLB", "filing_type": "10-K",
        "filing_date": "2024-02-27", "section": None, "chunk_type": "paragraph",
        "source_url": "https://sec.gov/x", "text": "Net income was $348.7 million.",
    }


def make_pipeline(monkeypatch, *, rerank=True, generation=True):
    """A real pipeline with fake collaborators — its own methods, nobody
    else's."""
    pipeline = object.__new__(DueDiligencePipeline)
    pipeline.config = None
    pipeline.client = object()
    pipeline.index_name = "duediligence-chunks"
    pipeline.embedder = FakeEmbedder()
    pipeline.enable_generation = generation
    pipeline.generation_backend = FakeBackend(
        "Net income was $348.7 million [1].", name="ollama", model="local-8b"
    )
    pipeline.reranker = FakeReranker() if rerank else None

    monkeypatch.setattr(
        "duediligence.pipeline.hybrid_search",
        lambda *a, **kw: [_hit(), _hit("c2")],
    )
    return pipeline


class TestSpanPrimitive:
    def test_nesting_is_recorded(self, spans):
        with span("outer"):
            with span("inner"):
                pass
        outer, inner = by_name(spans, "outer"), by_name(spans, "inner")
        assert inner.parent.span_id == outer.context.span_id

    def test_attributes_are_attached(self, spans):
        with span("s", k=10, model="bge"):
            pass
        assert by_name(spans, "s").attributes["k"] == 10
        assert by_name(spans, "s").attributes["model"] == "bge"

    def test_none_attributes_are_dropped_not_stringified(self, spans):
        # An absent filter and a filter of the literal text "None" are
        # different facts, and only one of them is true.
        with span("s", company=None, concept="NetIncomeLoss"):
            pass
        attributes = by_name(spans, "s").attributes
        assert "company" not in attributes
        assert attributes["concept"] == "NetIncomeLoss"


class TestDisabledTracing:
    def test_span_is_a_no_op_without_configuration(self):
        reset_tracing()
        with span("anything", attr=1) as active:
            active.set_attribute("late", 2)   # must not raise
            active.add_event("something")
        reset_tracing()

    def test_tracing_is_off_without_an_endpoint(self, monkeypatch):
        monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
        assert tracing_enabled() is False

    def test_an_explicit_off_switch_beats_a_configured_endpoint(self, monkeypatch):
        monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
        monkeypatch.setenv("DUEDILIGENCE_TRACING", "off")
        assert tracing_enabled() is False

    def test_configure_returns_false_when_no_endpoint_is_set(self, monkeypatch):
        monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
        reset_tracing()
        assert configure_tracing() is False
        reset_tracing()


class TestSemanticPathSpans:
    def test_every_stage_gets_its_own_span(self, spans, monkeypatch):
        make_pipeline(monkeypatch).answer("what were the merger terms?")

        emitted = names(spans)
        for stage in (
            "duediligence.answer", "route.classify", "retrieve",
            "embed.query", "rerank", "generate",
        ):
            assert stage in emitted, f"missing span: {stage}"

    def test_stages_nest_under_the_root(self, spans, monkeypatch):
        make_pipeline(monkeypatch).answer("what were the merger terms?")

        root = by_name(spans, "duediligence.answer")
        for child in ("route.classify", "retrieve", "generate"):
            assert by_name(spans, child).parent.span_id == root.context.span_id

    def test_embedding_and_rerank_nest_under_retrieval(self, spans, monkeypatch):
        make_pipeline(monkeypatch).answer("what were the merger terms?")

        retrieve = by_name(spans, "retrieve")
        for child in ("embed.query", "rerank"):
            assert by_name(spans, child).parent.span_id == retrieve.context.span_id

    def test_the_generation_span_records_which_model_answered(self, spans, monkeypatch):
        make_pipeline(monkeypatch).answer("what were the merger terms?")

        attributes = by_name(spans, "generate").attributes
        assert attributes["backend"] == "ollama"
        assert attributes["model"] == "local-8b"
        assert attributes["refused"] is False

    def test_no_generate_span_when_generation_is_disabled(self, spans, monkeypatch):
        make_pipeline(monkeypatch, generation=False).answer("what were the merger terms?")
        assert "generate" not in names(spans)

    def test_no_rerank_span_when_reranking_is_disabled(self, spans, monkeypatch):
        make_pipeline(monkeypatch, rerank=False).answer("what were the merger terms?")
        assert "rerank" not in names(spans)
        assert "retrieve" in names(spans)


class TestTracingDoesNotChangeBehaviour:
    def test_the_result_is_identical_traced_and_untraced(self, monkeypatch):
        question = "what were the merger terms?"

        reset_tracing()
        untraced = make_pipeline(monkeypatch).answer(question)

        exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        configure_tracing(tracer_provider=provider)
        traced = make_pipeline(monkeypatch).answer(question)
        reset_tracing()

        assert isinstance(traced, PipelineResult)
        # latency_ms legitimately differs between runs; everything else must not.
        for field in ("question", "route", "answer", "citations", "passages", "refused"):
            assert traced[field] == untraced[field], f"tracing changed {field}"
