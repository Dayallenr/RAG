"""
A locally-served model as a generation backend.

This exists for one reason: arithmetic. The hosted free tier allows a
verified 20 requests/day on this key. Generating answers for the
101-question eval set therefore takes six days, and generating the ~4,000
synthetic training queries the fine-tuning needs would take **200 days**.
Neither is a tuning problem; they are impossible on a quota. A model running
on local hardware has no such ceiling, and both jobs collapse to one sitting.

The second benefit is structural rather than practical. Once generation runs
locally, the hosted model is free to act purely as an *independent judge* of
those answers — which is the arrangement ``generate/backends.py`` exists to
make possible and ``eval/run_groundedness_eval.py`` records in its report.

**Talks to Ollama's native API rather than its OpenAI-compatible one.**
Both work. The native endpoint needs only ``requests``, which this project
already depends on, where the compatible route would add an SDK for no gain
at this size.

**Reasoning traces are stripped.** Current instruct models — Qwen3 among
them — may emit a ``<think>...</think>`` block before their actual answer.
Left in, that block would be parsed as part of the answer: it would be
scored by the groundedness judge, and it would be embedded as a synthetic
training query. It is removed here, once, rather than at each call site.
"""
from __future__ import annotations

import logging
import os
import re

import requests

logger = logging.getLogger(__name__)

__all__ = ["DEFAULT_HOST", "OllamaBackend", "strip_reasoning"]

DEFAULT_HOST = "http://localhost:11434"

# Generation on a consumer GPU is slow compared with a hosted API, and a
# long prompt with a large context can genuinely take minutes. A short
# timeout here would look like a model failure when it is a client giving up.
_DEFAULT_TIMEOUT = 600

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_UNCLOSED_THINK_RE = re.compile(r"^.*?</think>", re.DOTALL | re.IGNORECASE)


def strip_reasoning(text: str) -> str:
    """Remove a model's reasoning block from its response.

    Handles the unclosed case too — a response truncated by a token limit can
    contain an opening ``<think>`` and no closing tag, and treating that
    whole thing as an answer would be worse than returning nothing.
    """
    cleaned = _THINK_RE.sub("", text)
    if "</think>" in cleaned:
        cleaned = _UNCLOSED_THINK_RE.sub("", cleaned)
    return cleaned.strip()


class OllamaBackend:
    """Generation against a local Ollama server."""

    name = "ollama"

    def __init__(
        self,
        model: str = "qwen3:8b",
        *,
        host: str | None = None,
        timeout: int = _DEFAULT_TIMEOUT,
        session: requests.Session | None = None,
        options: dict | None = None,
    ) -> None:
        self.model = model
        self.host = (host or os.environ.get("OLLAMA_HOST") or DEFAULT_HOST).rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()
        # Temperature 0 by default: both callers want reproducible output.
        # An eval whose answers change between runs cannot be resumed
        # meaningfully, and synthetic training data should be regenerable.
        self.options = {"temperature": 0.0} | (options or {})

    def generate(self, prompt: str) -> str:
        response = self._session.post(
            f"{self.host}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "think": False,  # ignored by non-reasoning models
                "options": self.options,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return strip_reasoning(response.json().get("response", "") or "")

    def describe(self) -> dict[str, str]:
        return {"backend": self.name, "model": self.model}

    def available(self) -> bool:
        """Is the server up and does it have this model pulled?

        Checked before a long run rather than discovered partway through it:
        a typo in a model name should fail in one second, not after the first
        forty questions have already been generated.
        """
        try:
            response = self._session.get(f"{self.host}/api/tags", timeout=10)
            response.raise_for_status()
        except requests.RequestException as error:
            logger.warning("ollama unreachable at %s (%s)", self.host, error)
            return False

        pulled = {m.get("name", "") for m in response.json().get("models", [])}
        if self.model in pulled or f"{self.model}:latest" in pulled:
            return True
        logger.warning(
            "ollama at %s has no model %r; pulled: %s",
            self.host, self.model, ", ".join(sorted(pulled)) or "(none)",
        )
        return False
