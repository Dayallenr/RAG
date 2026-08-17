"""Tests for the local generation backend.

No test starts a server. The HTTP session is injected, which keeps these
hermetic and means CI — which has no GPU and no Ollama — runs them too.
"""
from __future__ import annotations

import pytest
import requests

from duediligence.generate.backends import TextGenerationBackend, backends_are_independent
from duediligence.generate.ollama_backend import OllamaBackend, strip_reasoning


class FakeResponse:
    def __init__(self, payload, *, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")


class FakeSession:
    def __init__(self, post_payload=None, get_payload=None, *, post_error=None):
        # `is None`, not `or`: an empty payload is a case under test, and
        # `{} or default` would silently substitute the default for it.
        self.post_payload = {"response": "an answer"} if post_payload is None else post_payload
        self.get_payload = (
            {"models": [{"name": "qwen3:8b"}]} if get_payload is None else get_payload
        )
        self.posts: list[dict] = []
        self._post_error = post_error

    def post(self, url, *, json, timeout):
        if self._post_error:
            raise self._post_error
        self.posts.append({"url": url, "json": json, "timeout": timeout})
        return FakeResponse(self.post_payload)

    def get(self, url, *, timeout):
        if self._post_error:
            raise self._post_error
        return FakeResponse(self.get_payload)


class TestStripReasoning:
    def test_removes_a_think_block(self):
        assert strip_reasoning("<think>hmm, let me see</think>The answer is 42.") == (
            "The answer is 42."
        )

    def test_leaves_ordinary_text_alone(self):
        assert strip_reasoning("The answer is 42.") == "The answer is 42."

    def test_handles_an_unclosed_opening_tag(self):
        # A response truncated mid-reasoning would otherwise be scored as if
        # the reasoning were the answer.
        assert strip_reasoning("<think>reasoning\nmore reasoning") == (
            "<think>reasoning\nmore reasoning"
        )

    def test_handles_reasoning_with_no_opening_tag(self):
        # Some servers strip the opening tag but not the closing one.
        assert strip_reasoning("stray reasoning</think>Real answer.") == "Real answer."

    def test_removes_multiple_blocks(self):
        assert strip_reasoning("<think>a</think>One.<think>b</think>Two.") == "One.Two."

    def test_multiline_reasoning_is_removed(self):
        assert strip_reasoning("<think>\nline1\nline2\n</think>\nAnswer.") == "Answer."


class TestOllamaBackend:
    def test_satisfies_the_backend_protocol(self):
        assert isinstance(OllamaBackend(session=FakeSession()), TextGenerationBackend)

    def test_posts_the_prompt_and_returns_the_response(self):
        session = FakeSession({"response": "Net income was $348.7 million [1]."})
        backend = OllamaBackend("qwen3:8b", host="http://pc:11434", session=session)

        assert backend.generate("a prompt") == "Net income was $348.7 million [1]."
        sent = session.posts[0]
        assert sent["url"] == "http://pc:11434/api/generate"
        assert sent["json"]["model"] == "qwen3:8b"
        assert sent["json"]["prompt"] == "a prompt"
        assert sent["json"]["stream"] is False

    def test_reasoning_is_stripped_from_generated_text(self):
        session = FakeSession({"response": "<think>plan</think>The merger closed in 2023."})
        backend = OllamaBackend(session=session)
        assert backend.generate("p") == "The merger closed in 2023."

    def test_defaults_to_deterministic_output(self):
        # A resumable eval and regenerable training data both need this.
        session = FakeSession()
        OllamaBackend(session=session).generate("p")
        assert session.posts[0]["json"]["options"]["temperature"] == 0.0

    def test_options_can_be_overridden(self):
        session = FakeSession()
        OllamaBackend(session=session, options={"temperature": 0.8, "num_ctx": 8192}).generate("p")
        options = session.posts[0]["json"]["options"]
        assert options["temperature"] == 0.8
        assert options["num_ctx"] == 8192

    def test_a_missing_response_field_becomes_an_empty_string(self):
        assert OllamaBackend(session=FakeSession({})).generate("p") == ""

    def test_host_comes_from_the_environment_when_unset(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_HOST", "http://192.168.1.50:11434")
        assert OllamaBackend(session=FakeSession()).host == "http://192.168.1.50:11434"

    def test_an_explicit_host_beats_the_environment(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_HOST", "http://from-env:11434")
        backend = OllamaBackend(host="http://explicit:11434", session=FakeSession())
        assert backend.host == "http://explicit:11434"

    def test_a_trailing_slash_on_the_host_does_not_double_up(self):
        session = FakeSession()
        OllamaBackend(host="http://pc:11434/", session=session).generate("p")
        assert session.posts[0]["url"] == "http://pc:11434/api/generate"

    def test_an_http_error_propagates_rather_than_returning_empty(self):
        # A silent empty answer would be recorded as a refusal and pollute
        # the groundedness numbers.
        session = FakeSession(post_error=requests.ConnectionError("refused"))
        with pytest.raises(requests.ConnectionError):
            OllamaBackend(session=session).generate("p")

    def test_describe_reports_backend_and_model(self):
        assert OllamaBackend("qwen3:8b", session=FakeSession()).describe() == {
            "backend": "ollama",
            "model": "qwen3:8b",
        }


class TestAvailability:
    def test_available_when_the_model_is_pulled(self):
        session = FakeSession(get_payload={"models": [{"name": "qwen3:8b"}]})
        assert OllamaBackend("qwen3:8b", session=session).available() is True

    def test_a_latest_tag_counts_as_pulled(self):
        session = FakeSession(get_payload={"models": [{"name": "qwen3:8b:latest"}]})
        assert OllamaBackend("qwen3:8b", session=session).available() is True

    def test_unavailable_when_the_model_is_missing(self):
        # Should fail in a second, not forty questions into a long run.
        session = FakeSession(get_payload={"models": [{"name": "llama3:8b"}]})
        assert OllamaBackend("qwen3:8b", session=session).available() is False

    def test_unavailable_when_the_server_is_unreachable(self):
        session = FakeSession(post_error=requests.ConnectionError("refused"))
        assert OllamaBackend(session=session).available() is False


def test_a_local_generator_is_independent_of_a_hosted_judge():
    """The whole point of running generation locally: the hosted model is
    then free to judge those answers as a genuinely different model."""
    from duediligence.generate.backends import GeminiBackend

    assert backends_are_independent(
        OllamaBackend("qwen3:8b", session=FakeSession()),
        GeminiBackend("gemini-flash-latest"),
    )
