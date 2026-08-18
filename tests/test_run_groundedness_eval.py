"""Tests for the groundedness eval: judging, summarising, and — the point of
the backend seam — keeping the judge separable from the generator.

Judging a model's output with the same model shares a failure mode: a claim
both find plausible is marked supported. The seam does not fix that on its
own, but it makes independence arrangeable and, here, observable in the
report rather than left as an assumption.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from duediligence.eval.run_groundedness_eval import (
    guard_judgment_regression,
    judge_groundedness,
    run_groundedness_eval,
    summarize,
)
from tests.fakes import FakeBackend


class FakePipeline:
    """Stands in for the real pipeline so this runs with no OpenSearch
    cluster and no embedding model. Carries its own generation backend,
    exactly as the real one does."""

    def __init__(self, backend, *, answer: str = "Net income was $348.7 million [1]."):
        self.generation_backend = backend
        self.questions: list[str] = []
        self._answer = answer

    def answer(self, question: str) -> dict:
        self.questions.append(question)
        return {
            "route": "semantic",
            "answer": self._answer,
            "refused": False,
            "citations": [{"number": 1, "chunk_id": "c1"}],
            "passages": [
                {"chunk_id": "c1", "text": "The filing states net income of $348.7 million."}
            ],
        }


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


class TestBackendWiring:
    """Without these, swapping ``generation_backend`` and ``judge_backend``
    at the call sites produces a green suite and a report whose provenance is
    exactly backwards."""

    @staticmethod
    def _eval_set(tmp_path, question="what was net income?"):
        path = tmp_path / "eval.jsonl"
        path.write_text(json.dumps({"eval_id": "r001", "question": question}) + "\n")
        return path

    def test_the_judge_backend_judges_and_the_generator_does_not(self, tmp_path, monkeypatch):
        monkeypatch.setattr(time, "sleep", lambda *_args, **_kw: None)
        generator = FakeBackend(name="ollama", model="local-8b")
        judge = FakeBackend(_verdict(total=1, supported=1),
                            name="gemini", model="gemini-flash-latest")

        run_groundedness_eval(
            str(self._eval_set(tmp_path)), str(tmp_path / "answers.jsonl"),
            judge_backend=judge, pipeline=FakePipeline(generator),
        )

        assert len(judge.prompts) == 1
        assert "Net income was $348.7 million" in judge.prompts[0]
        # The generator is used by the pipeline, never for judging.
        assert generator.prompts == []

    def test_the_report_names_the_model_the_pipeline_actually_used(self, tmp_path, monkeypatch):
        # The provenance block must reflect the pipeline that ran, not the
        # backend defaulted inside the eval — otherwise it can claim an
        # independent judge that never existed.
        monkeypatch.setattr(time, "sleep", lambda *_args, **_kw: None)
        judge = FakeBackend(_verdict(), name="gemini", model="gemini-flash-latest")

        report = run_groundedness_eval(
            str(self._eval_set(tmp_path)), str(tmp_path / "answers.jsonl"),
            judge_backend=judge,
            pipeline=FakePipeline(FakeBackend(name="ollama", model="local-8b")),
        )

        judging = report["judging"]
        assert judging["generation"]["model"] == "local-8b"
        assert judging["judge"]["model"] == "gemini-flash-latest"
        assert judging["independent_judge"] is True

    def test_the_question_reaches_the_pipeline(self, tmp_path, monkeypatch):
        monkeypatch.setattr(time, "sleep", lambda *_args, **_kw: None)
        pipeline = FakePipeline(FakeBackend(name="ollama", model="local-8b"))

        run_groundedness_eval(
            str(self._eval_set(tmp_path, "how big were deposits?")),
            str(tmp_path / "answers.jsonl"),
            judge_backend=FakeBackend(_verdict()), pipeline=pipeline,
        )

        assert pipeline.questions == ["how big were deposits?"]

    def test_completed_answers_are_skipped_on_a_rerun(self, tmp_path, monkeypatch):
        # Resumability is what keeps a 20-requests/day quota from being spent
        # redoing finished work.
        monkeypatch.setattr(time, "sleep", lambda *_args, **_kw: None)
        eval_set, answers = self._eval_set(tmp_path), tmp_path / "answers.jsonl"
        pipeline = FakePipeline(FakeBackend(name="ollama", model="local-8b"))

        for _ in range(2):
            run_groundedness_eval(str(eval_set), str(answers),
                                  judge_backend=FakeBackend(_verdict()), pipeline=pipeline)

        assert len(pipeline.questions) == 1
        assert len(answers.read_text().strip().splitlines()) == 1


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


class TestJudgmentRegressionGuard:
    """A run that judges nothing must not overwrite a report that judged
    something.

    This is not hypothetical. On 2026-08-18 this module was run on the Mac,
    where Ollama is not installed, so ``default_generation_backend`` returned
    Gemini for *both* roles, ``backends_are_independent`` was False, judging
    was skipped — and the resulting ``judged_answers: 0`` report overwrote one
    recording 9 judgments and was logged to the experiment tracker as the
    newest run. Nothing errored. The guard turns that silent regression into
    a stop.
    """

    def _report(self, judged: int) -> dict:
        return {"judged_answers": judged, "mean_claim_support_rate": None}

    def test_missing_report_is_not_a_regression(self, tmp_path):
        target = tmp_path / "report.json"
        guard_judgment_regression(self._report(0), target)

    def test_writing_more_judgments_is_allowed(self, tmp_path):
        target = tmp_path / "report.json"
        target.write_text(json.dumps(self._report(9)))
        guard_judgment_regression(self._report(14), target)

    def test_writing_the_same_count_is_allowed(self, tmp_path):
        target = tmp_path / "report.json"
        target.write_text(json.dumps(self._report(9)))
        guard_judgment_regression(self._report(9), target)

    def test_dropping_judgments_raises_and_names_the_right_script(self, tmp_path):
        target = tmp_path / "report.json"
        target.write_text(json.dumps(self._report(9)))

        with pytest.raises(SystemExit) as excinfo:
            guard_judgment_regression(self._report(0), target)

        message = str(excinfo.value)
        assert "9" in message and "0" in message
        # The whole point of stopping is to send the reader somewhere that works.
        assert "judge_answers.py" in message

    def test_an_unreadable_existing_report_does_not_block_the_write(self, tmp_path):
        target = tmp_path / "report.json"
        target.write_text("{ this is not json")
        guard_judgment_regression(self._report(0), target)


class TestGuardIsWiredIntoMain:
    """The guard must run on the real command path, not merely exist.

    Deleting the ``guard_judgment_regression(...)`` call from ``main`` leaves
    every test in ``TestJudgmentRegressionGuard`` green — verified by doing
    it — while the actual command overwrites a 14-judgment report with a
    0-judgment one and exits 0. That is the same class of gap the #11 code
    review caught in ``tests/test_finetune_args.py``: asserting on the
    parsed arguments rather than on what reaches the trainer. These tests
    drive ``main`` itself.
    """

    def _run_main(self, monkeypatch, tmp_path, *, report: dict, out: Path):
        import duediligence.eval.run_groundedness_eval as module

        logged: list = []
        monkeypatch.setattr(module, "run_groundedness_eval", lambda *a, **k: dict(report))
        monkeypatch.setattr(module, "log_run", lambda **k: logged.append(k))
        monkeypatch.setattr(
            "sys.argv", ["run_groundedness_eval", "--out", str(out), "--answers", str(tmp_path / "a.jsonl")],
        )
        module.main()
        return logged

    def _stub(self, judged: int) -> dict:
        # Carries every field main() prints, so a passing test means main()
        # actually ran to completion rather than dying on a missing key.
        return {
            "judged_answers": judged,
            "split": "all",
            "questions_in_eval_set": 101,
            "answers_generated": 101,
            "coverage": 1.0,
            "structured_route": 12,
            "semantic_route": 89,
            "refusals": 21,
            "refusal_rate": 0.236,
            "answers_with_valid_citations": 68,
            "citation_coverage": 1.0,
            "mean_claim_support_rate": 0.786 if judged else None,
            "fully_supported_answers": 11 if judged else 0,
            "judging": {
                "generation": {"backend": "x", "model": "m"},
                "judge": {"backend": "y", "model": "n"},
                "independent_judge": True,
            },
        }

    def test_main_refuses_and_leaves_the_existing_report_untouched(
        self, monkeypatch, tmp_path
    ):
        out = tmp_path / "report.json"
        original = json.dumps(self._stub(14), indent=2)
        out.write_text(original)

        with pytest.raises(SystemExit):
            self._run_main(monkeypatch, tmp_path, report=self._stub(0), out=out)

        # The file on disk is the thing being protected.
        assert out.read_text() == original

    def test_main_does_not_log_a_regressed_run_to_the_tracker(
        self, monkeypatch, tmp_path
    ):
        out = tmp_path / "report.json"
        out.write_text(json.dumps(self._stub(14)))

        logged = []
        with pytest.raises(SystemExit):
            logged = self._run_main(monkeypatch, tmp_path, report=self._stub(0), out=out)

        # A stub reaching the tracker becomes the newest run of its name and
        # is what verify_wandb_runs.py would then cite.
        assert logged == []

    def test_main_still_writes_when_the_count_grows(self, monkeypatch, tmp_path):
        out = tmp_path / "report.json"
        out.write_text(json.dumps(self._stub(9)))

        self._run_main(monkeypatch, tmp_path, report=self._stub(14), out=out)

        assert json.loads(out.read_text())["judged_answers"] == 14
