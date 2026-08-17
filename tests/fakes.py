"""Shared test doubles.

The fake backend lives here rather than in one test module because two
different modules need it — answer generation and groundedness judging —
and the whole point of the backend seam is that those two can be given
*different* backends. A fake that only one of them could import would make
that property awkward to test, which is the property most worth testing.

Nothing here touches the network. That is not just hermeticity for its own
sake: the hosted model's free tier allows 20 requests per day, and a suite
that spent them would make the groundedness eval unrunnable for the rest of
the day (see CLAUDE.md).
"""
from __future__ import annotations


class FakeBackend:
    """Records every prompt it is given and returns canned replies.

    Replies are consumed in order; once exhausted the last one repeats, so a
    test that only cares about the first call does not have to supply a reply
    per call.
    """

    def __init__(self, *replies: str, name: str = "fake", model: str = "fake-model") -> None:
        self.name = name
        self.model = model
        self.prompts: list[str] = []
        self._replies = list(replies) or [""]

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        index = min(len(self.prompts) - 1, len(self._replies) - 1)
        return self._replies[index]

    def describe(self) -> dict[str, str]:
        return {"backend": self.name, "model": self.model}
