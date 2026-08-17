"""Tests for the groundedness eval: judging, summarising, and — the point of
the backend seam — keeping the judge separable from the generator.

Judging a model's output with the same model shares a failure mode: a claim
both find plausible is marked supported. The seam does not fix that on its
own, but it makes independence arrangeable and, here, observable in the
report rather than left as an assumption.
"""
from __future__ import annotations

import json

import pytest

from duediligence.eval.run_groundedness_eval import judge_groundedness, summarize
from tests.fakes import FakeBackend


def _verdict(total=2, supported=2, unsupported=None):
    return json.dumps(
        {
            "total_claims": total,
            "supported_claims": supported,
            "unsupported": unsupported or [],
        }
    )


class TestJudgeGroundedness:
    def test_uses_the_injected_backend_and_parses_the_verdict(self):
        backend = FakeBackend(_verdict(total=4, supported=3))
        result = judge_groundedness("an answer", [{"text": "a passage"}], backend=backend)

        assert result["total_claims"] == 4
        assert result["supported_claims"] == 3
        assert result["support_rate"] == pytest.approx(0.75)
        assert len(backend.prompts) == 1

    def test_the_answer_and_passages_reach_the_judge(self):
        backend = FakeBackend(_verdict())
        judge_groundedness("net income was $348.7m", [{"text": "the filing says so"}],
                           backend=backend)

        prompt = backend.prompts[0]
        assert "net income was $348.7m" in prompt
        assert "the filing says so" in prompt

    def test_strips_markdown_fences_around_the_json(self):
        # Models wrap JSON in fences often enough that treating it as a
        # judging failure would lose real verdicts.
        backend = FakeBackend(f"```json\n{_verdict(total=1, supported=1)}\n```")
        assert judge_groundedness("a", [{"text": "p"}], backend=backend)["support_rate"] == 1.0

    def test_unparseable_output_is_an_error_marker_not_a_crash(self):
        backend = FakeBackend("I think it looks fine to me!")
        result = judge_groundedness("a", [{"text": "p"}], backend=backend)

        assert result["judge_error"] == "unparseable"
        assert "support_rate" not in result

    def test_zero_claims_does_not_divide_by_zero(self):
        backend = FakeBackend(_verdict(total=0, supported=0))
        assert judge_groundedness("a", [{"text": "p"}], backend=backend)["support_rate"] is None


class TestJudgeIndependence:
    def test_a_distinct_judge_backend_is_reported_as_independent(self):
        from duediligence.eval.run_groundedness_eval import describe_judging

        described = describe_judging(
            generation_backend=FakeBackend(name="ollama", model="local-8b"),
            judge_backend=FakeBackend(name="gemini", model="gemini-flash-latest"),
        )
        assert described["generation"]["model"] == "local-8b"
        assert described["judge"]["model"] == "gemini-flash-latest"
        assert described["independent_judge"] is True

    def test_judging_with_the_generator_is_reported_as_not_independent(self):
        # This is the current default, and the report must say so plainly
        # rather than letting a self-graded number look independent.
        from duediligence.eval.run_groundedness_eval import describe_judging

        same = FakeBackend(name="gemini", model="gemini-flash-latest")
        described = describe_judging(generation_backend=same, judge_backend=same)
        assert described["independent_judge"] is False


class TestGroundednessSummary:
    def test_summary_counts_routes_refusals_and_citations(self):
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
        summary = summarize([], total_questions=10)
        assert summary["answers_generated"] == 0
        assert summary["mean_claim_support_rate"] is None
