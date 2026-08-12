"""Tests for answer generation, citation enforcement, and the pipeline wiring.

No test here touches the network — the Gemini client is injected. That is
deliberate beyond the usual hermeticity argument: the free tier allows 20
requests per day, and a test suite that spent them would make the
groundedness eval unrunnable.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from duediligence.generate.answer import (
    REFUSAL_TEXT,
    build_prompt,
    generate_answer,
    parse_citations,
)


class StubGemini:
    """Returns a canned answer and records the prompt it was given."""

    def __init__(self, text):
        self.prompts = []
        self.models = SimpleNamespace(generate_content=self._generate)
        self._text = text

    def _generate(self, *, model, contents):
        self.prompts.append(contents)
        return SimpleNamespace(text=self._text)


def _passages(n=3):
    return [
        {
            "chunk_id": f"chunk{i}",
            "company": "COLB",
            "filing_type": "10-K",
            "filing_date": "2024-02-27",
            "section": "Item 7. MD&A",
            "source_url": f"https://www.sec.gov/x{i}.htm",
            "text": f"Passage {i} states net income of ${i}00 million.",
        }
        for i in range(1, n + 1)
    ]


class TestBuildPrompt:
    def test_passages_are_numbered_from_one(self):
        prompt = build_prompt("q", _passages(2))
        assert "[1] COLB 10-K" in prompt
        assert "[2] COLB 10-K" in prompt

    def test_passage_provenance_is_inline(self):
        # Several of these banks discuss the same events; a passage stripped
        # of its company invites cross-attribution.
        prompt = build_prompt("q", _passages(1))
        assert "COLB" in prompt
        assert "Item 7. MD&A" in prompt

    def test_prompt_instructs_refusal_over_guessing(self):
        assert REFUSAL_TEXT in build_prompt("q", _passages(1))


class TestParseCitations:
    def test_extracts_in_range_citations(self):
        citations = parse_citations("Net income rose [1] and deposits fell [3].", _passages(3))
        assert [c["number"] for c in citations] == [1, 3]
        assert citations[0]["chunk_id"] == "chunk1"

    def test_drops_out_of_range_citations(self):
        # [7] with three passages supplied is fabricated provenance.
        citations = parse_citations("Claim [7] and claim [2].", _passages(3))
        assert [c["number"] for c in citations] == [2]

    def test_does_not_remap_an_invalid_citation_to_a_real_chunk(self):
        citations = parse_citations("Only [9].", _passages(3))
        assert citations == []

    def test_deduplicates_repeated_citations(self):
        citations = parse_citations("[1] and again [1].", _passages(3))
        assert len(citations) == 1

    def test_citations_carry_source_urls(self):
        citations = parse_citations("[2]", _passages(3))
        assert citations[0]["source_url"] == "https://www.sec.gov/x2.htm"


class TestGenerateAnswer:
    def test_returns_answer_with_resolved_citations(self):
        client = StubGemini("Net income was $348.7 million [1].")
        result = generate_answer("q", _passages(3), model="m", client=client)
        assert result.answer.startswith("Net income")
        assert result.citations[0]["chunk_id"] == "chunk1"
        assert result.refused is False

    def test_empty_passages_refuse_without_calling_the_model(self):
        client = StubGemini("should never be used")
        result = generate_answer("q", [], model="m", client=client)
        # Calling the model with no context invites answering from memory.
        assert client.prompts == []
        assert result.refused is True
        assert result.answer == REFUSAL_TEXT

    def test_detects_a_refusal_from_the_model(self):
        client = StubGemini(REFUSAL_TEXT)
        assert generate_answer("q", _passages(2), model="m", client=client).refused is True

    def test_context_is_capped_at_max_passages(self):
        client = StubGemini("[1]")
        result = generate_answer("q", _passages(10), model="m", client=client, max_passages=4)
        assert len(result.context_chunk_ids) == 4
        assert "[5]" not in client.prompts[0]

    def test_serializes_for_the_api(self):
        client = StubGemini("Answer [1].")
        payload = generate_answer("q", _passages(2), model="m", client=client).to_dict()
        assert payload["route"] == "semantic"
        assert payload["context_chunk_ids"] == ["chunk1", "chunk2"]


class TestGroundednessSummary:
    def test_summary_counts_routes_refusals_and_citations(self):
        from duediligence.eval.run_groundedness_eval import summarize

        rows = [
            {"route": "structured"},
            {"route": "semantic", "refused": False, "citations": [{"number": 1}],
             "judge": {"support_rate": 1.0}},
            {"route": "semantic", "refused": False, "citations": [],
             "judge": {"support_rate": 0.5}},
            {"route": "semantic", "refused": True, "citations": []},
        ]
        summary = summarize(rows, total_questions=8)

        assert summary["structured_route"] == 1
        assert summary["semantic_route"] == 3
        assert summary["refusals"] == 1
        assert summary["answers_with_valid_citations"] == 1
        assert summary["mean_claim_support_rate"] == pytest.approx(0.75)
        assert summary["fully_supported_answers"] == 1
        assert summary["coverage"] == pytest.approx(0.5)

    def test_empty_run_does_not_divide_by_zero(self):
        from duediligence.eval.run_groundedness_eval import summarize

        summary = summarize([], total_questions=10)
        assert summary["answers_generated"] == 0
        assert summary["mean_claim_support_rate"] is None
