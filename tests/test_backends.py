"""Tests for the text-generation backend seam.

The seam exists so that the model generating an answer and the model judging
that answer's groundedness can be different things. Before it existed, both
call sites reached for the same hosted client directly, which made judge
independence impossible to arrange and impossible to assert.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from duediligence.generate.backends import (
    GeminiBackend,
    TextGenerationBackend,
    backends_are_independent,
)
from tests.fakes import FakeBackend


class StubGenAIClient:
    """Mimics the shape of the hosted SDK client: client.models.generate_content."""

    def __init__(self, text: str | None) -> None:
        self.calls: list[dict] = []
        self.models = SimpleNamespace(generate_content=self._generate)
        self._text = text

    def _generate(self, *, model, contents):
        self.calls.append({"model": model, "contents": contents})
        return SimpleNamespace(text=self._text)


class TestProtocol:
    def test_a_fake_satisfies_the_backend_protocol(self):
        assert isinstance(FakeBackend(), TextGenerationBackend)

    def test_the_hosted_backend_satisfies_the_protocol(self):
        assert isinstance(GeminiBackend("some-model"), TextGenerationBackend)


class TestGeminiBackend:
    def test_generate_passes_its_own_model_and_returns_the_text(self):
        client = StubGenAIClient("an answer")
        backend = GeminiBackend("gemini-flash-latest", client=client)

        assert backend.generate("a prompt") == "an answer"
        assert client.calls == [{"model": "gemini-flash-latest", "contents": "a prompt"}]

    def test_generate_strips_surrounding_whitespace(self):
        backend = GeminiBackend("m", client=StubGenAIClient("  padded\n"))
        assert backend.generate("p") == "padded"

    def test_a_none_response_becomes_an_empty_string(self):
        # The SDK returns text=None when a response is blocked or empty;
        # callers downstream do string operations on this.
        backend = GeminiBackend("m", client=StubGenAIClient(None))
        assert backend.generate("p") == ""

    def test_constructing_the_backend_does_not_require_an_api_key(self):
        # Construction must stay lazy: the pipeline builds a backend at
        # startup, and an environment without a key should still be able to
        # serve retrieval-only requests.
        backend = GeminiBackend("m")
        assert backend.model == "m"

    def test_describe_reports_backend_and_model(self):
        assert GeminiBackend("gemini-flash-latest").describe() == {
            "backend": "gemini",
            "model": "gemini-flash-latest",
        }


class TestIndependence:
    def test_two_different_models_are_independent(self):
        assert backends_are_independent(
            FakeBackend(model="local-8b", name="ollama"),
            FakeBackend(model="gemini-flash-latest", name="gemini"),
        )

    def test_the_same_backend_object_is_not_independent_of_itself(self):
        backend = FakeBackend(model="m", name="n")
        assert not backends_are_independent(backend, backend)

    def test_same_model_on_the_same_backend_is_not_independent(self):
        # Two client objects pointed at one model is the situation the seam
        # exists to make visible — it is not an independent judge.
        assert not backends_are_independent(
            FakeBackend(model="gemini-flash-latest", name="gemini"),
            FakeBackend(model="gemini-flash-latest", name="gemini"),
        )


class TestFakeBackend:
    def test_records_prompts_and_returns_replies_in_order(self):
        backend = FakeBackend("first", "second")
        assert backend.generate("p1") == "first"
        assert backend.generate("p2") == "second"
        assert backend.prompts == ["p1", "p2"]

    def test_the_last_reply_repeats_once_replies_are_exhausted(self):
        backend = FakeBackend("only")
        assert [backend.generate("a"), backend.generate("b")] == ["only", "only"]

    def test_defaults_to_an_empty_reply(self):
        assert FakeBackend().generate("p") == ""


@pytest.mark.parametrize("backend", [FakeBackend(), GeminiBackend("m")])
def test_every_backend_exposes_name_and_model(backend):
    assert isinstance(backend.name, str) and backend.name
    assert isinstance(backend.model, str) and backend.model
