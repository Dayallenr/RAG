"""
Text-generation backends: one small interface, several models behind it.

Answer generation and groundedness judging were both handed the hosted
Gemini client: the groundedness eval constructed one and passed the same
object to the pipeline and to the judge. So the generator and the judge were
the same *model* by construction — and judging a model's output with that
same model shares a failure mode, because a claim both find plausible gets
marked supported. The seam here does not fix that on its own; what it does
is make independence arrangeable, and make it visible in the report instead
of leaving it as an assumption a reader has to take on trust.

The second reason this exists is quota. The hosted free tier allows a
verified 20 requests/day on this key — confirmed by an actual 429, not by
documentation (see docs/local-generation.md) — which is not enough to
generate answers for a 101-question eval set — one pass would take five days
of wall-clock. A locally-served model has no such ceiling. Swapping one in
should be a constructor argument, not a rewrite of the generation path, and
with this interface it is.

The interface is deliberately one method. Everything this project asks of a
language model is "here is a prompt, give me text back": no streaming, no
tool calls, no multi-turn state. A wider interface would be speculative, and
each extra method is another thing every future backend has to implement.

Note that chart/image understanding (``ingest/chunk_charts.py``) is *not*
routed through here. It is multimodal rather than text-in/text-out, and
folding it in would widen this interface for one caller.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

__all__ = [
    "GeminiBackend",
    "TextGenerationBackend",
    "backends_are_independent",
    "default_generation_backend",
]


@runtime_checkable
class TextGenerationBackend(Protocol):
    """A model that turns a prompt into text.

    ``name`` identifies the provider and ``model`` the specific model. Both
    are part of the interface rather than implementation detail because the
    groundedness report records them: an independence claim that cannot be
    traced to two named models is not worth much.
    """

    name: str
    model: str

    def generate(self, prompt: str) -> str: ...

    def describe(self) -> dict[str, str]: ...


class GeminiBackend:
    """The hosted Gemini model — the original and, for now, default backend.

    The client is constructed lazily rather than in ``__init__`` because the
    serving pipeline builds a backend at startup, and an environment with no
    API key should still be able to serve retrieval-only requests instead of
    failing to boot. It also keeps constructing a backend free in tests.
    """

    name = "gemini"

    def __init__(self, model: str, *, client=None) -> None:
        self.model = model
        self._client = client

    def _get_client(self):
        if self._client is None:
            from duediligence.generate.gemini_client import get_client

            self._client = get_client()
        return self._client

    def generate(self, prompt: str) -> str:
        response = self._get_client().models.generate_content(
            model=self.model, contents=prompt
        )
        # The SDK returns text=None for a blocked or empty response, and
        # every caller downstream does string operations on this.
        return (response.text or "").strip()

    def describe(self) -> dict[str, str]:
        return {"backend": self.name, "model": self.model}


def default_generation_backend(config) -> TextGenerationBackend:
    """The backend used when a caller does not choose one.

    Holds the "hosted Gemini unless told otherwise" policy in exactly one
    place. It was previously spelled out at each call site, which is the kind
    of duplication that lets the serving path and the eval path drift onto
    different models without anyone noticing — precisely the confusion this
    module exists to remove.
    """
    return GeminiBackend(config.models.generation_model)


def backends_are_independent(
    generation: TextGenerationBackend, judge: TextGenerationBackend
) -> bool:
    """Is the judge genuinely a different model from the generator?

    Compares provider and model rather than object identity: two separately
    constructed clients pointed at the same model are not an independent
    judge, however different the objects are.
    """
    return (generation.name, generation.model) != (judge.name, judge.model)
