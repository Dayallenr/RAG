"""
Answer generation over retrieved context, with mandatory citations.

The pipeline this sits at the end of:

    query -> route (structured | semantic)
          -> structured: exact XBRL lookup, no model involved at all
          -> semantic:  hybrid retrieval -> rerank -> generate with citations

**The structured route does not call a model.** If the router identifies a
(concept, company, year) lookup, the answer is the XBRL value, formatted,
with the accession number it came from. Passing an exact figure through a
language model to have it restated in prose can only introduce error, and
it would spend one of the 20 daily Gemini requests to do so.

**Citations are enforced structurally, not requested politely.** Context
passages are numbered, the model is instructed to cite by number, and
``parse_citations`` extracts them and drops any that point at a passage that
was not supplied. A citation to `[7]` when six passages were given is a
hallucinated source, and it is discarded rather than shown to a user. What
survives is a set of citations that provably resolve to real chunks with
real sec.gov URLs.

**The prompt tells the model to refuse rather than guess.** For a
due-diligence tool, "the provided filings do not state this" is a correct
and useful answer; an invented figure is a catastrophic one. The
groundedness eval in ``eval/run_groundedness_eval.py`` measures whether
this actually holds.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

__all__ = [
    "GeneratedAnswer",
    "build_prompt",
    "generate_answer",
    "parse_citations",
]

_CITATION_RE = re.compile(r"\[(\d+)\]")

# Enough context to answer without burying the model. Reranked hits fall off
# in relevance quickly, and every extra passage is prompt tokens spent.
_DEFAULT_CONTEXT_PASSAGES = 6

_SYSTEM_INSTRUCTION = """\
You are a due-diligence analyst answering questions about SEC filings from \
US regional banks. You are given numbered passages extracted from real \
filings.

Rules:
1. Answer ONLY from the numbered passages provided. Do not use outside \
knowledge about these companies.
2. Cite every factual claim with the passage number in square brackets, \
like [1] or [2][3].
3. If the passages do not contain the answer, say exactly: "The provided \
filings do not state this." Do not guess, and do not fill gaps from memory.
4. Quote figures exactly as they appear. Do not round, convert, or \
recalculate them.
5. Be concise — a few sentences unless the question needs more.
"""


@dataclass(frozen=True)
class GeneratedAnswer:
    question: str
    answer: str
    citations: list[dict[str, Any]] = field(default_factory=list)
    route: str = "semantic"
    refused: bool = False
    model: str | None = None
    context_chunk_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "answer": self.answer,
            "citations": self.citations,
            "route": self.route,
            "refused": self.refused,
            "model": self.model,
            "context_chunk_ids": self.context_chunk_ids,
        }


def build_prompt(question: str, passages: list[dict[str, Any]]) -> str:
    """Render numbered context passages plus the question.

    Each passage carries its company, filing type and date inline, because
    several of these banks discuss the same events and a passage stripped of
    its provenance invites the model to attribute one bank's figures to
    another.
    """
    blocks = []
    for index, passage in enumerate(passages, start=1):
        header = (
            f"[{index}] {passage.get('company', '?')} "
            f"{passage.get('filing_type', '?')} filed {passage.get('filing_date', '?')}"
        )
        if passage.get("section"):
            header += f" — {passage['section']}"
        blocks.append(f"{header}\n{passage.get('text', '').strip()}")

    return (
        f"{_SYSTEM_INSTRUCTION}\n"
        f"--- PASSAGES ---\n\n"
        + "\n\n".join(blocks)
        + f"\n\n--- QUESTION ---\n{question}\n\n--- ANSWER ---\n"
    )


def parse_citations(answer: str, passages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract `[n]` citations, keeping only those that resolve to a passage.

    Out-of-range numbers are dropped, not repaired: a citation to a passage
    that was never supplied is a fabricated source, and silently remapping it
    to a real chunk would manufacture provenance that does not exist.
    """
    citations = []
    seen: set[int] = set()
    for match in _CITATION_RE.finditer(answer):
        number = int(match.group(1))
        if number in seen or not (1 <= number <= len(passages)):
            if not (1 <= number <= len(passages)):
                logger.warning(
                    "dropping citation [%d]: only %d passages supplied", number, len(passages)
                )
            continue
        seen.add(number)
        passage = passages[number - 1]
        citations.append(
            {
                "number": number,
                "chunk_id": passage.get("chunk_id"),
                "company": passage.get("company"),
                "filing_type": passage.get("filing_type"),
                "filing_date": passage.get("filing_date"),
                "section": passage.get("section"),
                "source_url": passage.get("source_url"),
            }
        )
    return citations


REFUSAL_TEXT = "The provided filings do not state this."


def generate_answer(
    question: str,
    passages: list[dict[str, Any]],
    *,
    model: str,
    client=None,
    max_passages: int = _DEFAULT_CONTEXT_PASSAGES,
) -> GeneratedAnswer:
    """Generate a cited answer from retrieved passages.

    ``client`` is injectable so tests never touch the network — and so the
    20-requests/day free-tier quota is not spent on unit tests.
    """
    passages = passages[:max_passages]

    if not passages:
        # No retrieval results means there is nothing to ground an answer
        # in. Calling the model here would invite it to answer from memory,
        # which is the one thing this system must not do.
        return GeneratedAnswer(
            question=question, answer=REFUSAL_TEXT, route="semantic",
            refused=True, model=None, context_chunk_ids=[],
        )

    if client is None:
        from duediligence.generate.gemini_client import get_client

        client = get_client()

    prompt = build_prompt(question, passages)
    response = client.models.generate_content(model=model, contents=prompt)
    text = (response.text or "").strip()

    return GeneratedAnswer(
        question=question,
        answer=text,
        citations=parse_citations(text, passages),
        route="semantic",
        refused=REFUSAL_TEXT.lower().rstrip(".") in text.lower(),
        model=model,
        context_chunk_ids=[p.get("chunk_id") for p in passages],
    )
