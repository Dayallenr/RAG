"""API tests against a stubbed pipeline.

The pipeline is replaced rather than constructed: a real one loads two
transformer models and needs a live OpenSearch, which would make these
tests slow, non-hermetic, and unrunnable in CI.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from duediligence.api.app import create_app, get_pipeline


class StubPipeline:
    def __init__(self, *, reachable=True, raises=False):
        self.index_name = "duediligence-chunks"
        self.calls = []
        self._raises = raises
        self.client = self  # readyz calls pipeline.client.indices.exists
        self.indices = self
        self._reachable = reachable

    def exists(self, *, index):
        if self._reachable is Ellipsis:
            raise RuntimeError("connection refused")
        return self._reachable

    def answer(self, question, *, k=6, filters=None):
        if self._raises:
            raise RuntimeError("boom")
        self.calls.append(("answer", question, k, filters))
        return {
            "question": question,
            "route": "structured" if "net income" in question else "semantic",
            "routing_reasons": ["stub"],
            "answer": "stub answer [1]",
            "structured_fact": None,
            "citations": [{"number": 1, "chunk_id": "c1"}],
            "passages": [{"chunk_id": "c1", "text": "t"}],
            "refused": False,
            "latency_ms": 1.0,
        }

    def retrieve(self, query, *, k=10, filters=None):
        if self._raises:
            raise RuntimeError("boom")
        self.calls.append(("retrieve", query, k, filters))
        return [
            {
                "chunk_id": "c1", "score": 0.9, "company": "COLB", "filing_type": "10-K",
                "filing_date": "2024-02-27", "section": None, "chunk_type": "paragraph",
                "source_url": "https://sec.gov/x", "text": "text",
            }
        ]


def make_client(pipeline=None):
    app = create_app()
    stub = pipeline or StubPipeline()
    app.dependency_overrides[get_pipeline] = lambda: stub
    app.state.pipeline = stub
    return TestClient(app), stub


class TestOps:
    def test_healthz_does_not_touch_opensearch(self):
        # Liveness must stay green during a search outage, or Kubernetes
        # restarts pods for a problem restarting cannot fix.
        client, _ = make_client(StubPipeline(reachable=Ellipsis))
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_readyz_is_ready_when_the_index_exists(self):
        client, _ = make_client()
        assert client.get("/readyz").status_code == 200

    def test_readyz_fails_when_the_index_is_missing(self):
        client, _ = make_client(StubPipeline(reachable=False))
        assert client.get("/readyz").status_code == 503

    def test_readyz_fails_when_opensearch_is_unreachable(self):
        client, _ = make_client(StubPipeline(reachable=Ellipsis))
        response = client.get("/readyz")
        assert response.status_code == 503
        assert "unreachable" in response.json()["detail"]

    def test_metrics_endpoint_exposes_prometheus_text(self):
        client, _ = make_client()
        client.post("/ask", json={"question": "what were deposits in 2023"})
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "duediligence_requests_total" in response.text


class TestAsk:
    def test_returns_answer_and_citations(self):
        client, _ = make_client()
        response = client.post("/ask", json={"question": "what are the merger risks?"})
        assert response.status_code == 200
        body = response.json()
        assert body["answer"] == "stub answer [1]"
        assert body["citations"][0]["chunk_id"] == "c1"

    def test_passes_filters_through(self):
        client, stub = make_client()
        client.post("/ask", json={"question": "merger risks", "company": "colb", "filing_type": "10-K"})
        _, _, _, filters = stub.calls[-1]
        # Ticker is upper-cased because the index stores it that way; a
        # lower-case term filter would silently match nothing.
        assert filters == {"company": "COLB", "filing_type": "10-K"}

    @pytest.mark.parametrize("question", ["", "ab"])
    def test_rejects_too_short_questions(self, question):
        client, _ = make_client()
        assert client.post("/ask", json={"question": question}).status_code == 422

    def test_rejects_oversized_k(self):
        client, _ = make_client()
        assert client.post("/ask", json={"question": "valid question", "k": 999}).status_code == 422

    def test_pipeline_failure_becomes_a_500(self):
        client, _ = make_client(StubPipeline(raises=True))
        assert client.post("/ask", json={"question": "valid question"}).status_code == 500

    def test_missing_pipeline_returns_503_not_500(self):
        app = create_app()
        app.state.pipeline = None
        response = TestClient(app).post("/ask", json={"question": "valid question"})
        # The process is healthy; it just is not ready.
        assert response.status_code == 503


class TestSearch:
    def test_returns_hits_without_generation(self):
        client, _ = make_client()
        response = client.post("/search", json={"query": "credit losses", "k": 5})
        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 1
        assert body["results"][0]["source_url"].startswith("https://")

    def test_k_is_forwarded(self):
        client, stub = make_client()
        client.post("/search", json={"query": "credit losses", "k": 7})
        assert stub.calls[-1][2] == 7


class TestRoute:
    def test_exposes_the_routing_decision_and_reasoning(self):
        client, _ = make_client()
        response = client.get("/route", params={"question": "What was Columbia's net income for 2023?"})
        body = response.json()
        assert body["route"] == "structured"
        assert body["concept"] == "NetIncomeLoss"
        assert body["company"] == "COLB"
        assert body["fiscal_year"] == 2023
        assert body["reasons"]

    def test_narrative_question_routes_semantic(self):
        client, _ = make_client()
        response = client.get("/route", params={"question": "Why did net income fall at Columbia in 2023?"})
        assert response.json()["route"] == "semantic"
