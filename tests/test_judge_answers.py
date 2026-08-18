"""
Tests for the judging harness that is now the documented way to add
groundedness verdicts to already-generated answers.

Two properties matter here and neither is about judging quality. The report
this script writes carries an ``independent_judge`` claim, which is only
sound while every answer in the file came from one generator; and the script
is the recommended writer of ``results/generation/report.json``, so it must
not regress that file any more than the module entry point may.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "judge_answers.py"


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("judge_answers", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _answers(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "answers.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def _row(eval_id: str, generated_by: str | None, route: str = "semantic") -> dict:
    return {
        "eval_id": eval_id, "question": "q", "route": route, "answer": "a",
        "refused": False, "citations": [{"number": 1}], "n_passages": 1,
        "passage_chunk_ids": ["c1"], "generated_by": generated_by,
    }


def _run(script, monkeypatch, tmp_path, *, answers: Path, judgments: Path, out: Path):
    monkeypatch.setattr(script, "log_run", lambda **k: None)
    monkeypatch.setattr(sys, "argv", [
        "judge_answers", "--answers", str(answers), "--judgments", str(judgments),
        "--out", str(out), "--contexts", str(tmp_path / "ctx.jsonl"), "--report-only",
    ])
    script.main()


class TestMixedGeneratorProvenance:
    """A single ``independent_judge`` verdict cannot describe a file whose
    answers came from different models.

    The script reads the generator from the *first* labelled row and applies
    it to every row. That is sound for a file one model wrote, and wrong the
    moment a second model appends to it — which
    ``duediligence.eval.run_groundedness_eval`` can do, on a machine where its
    generation backend resolves to the same hosted model that judges. The
    answer would then be reported as written by the local model and judged
    independently by the hosted one, when in fact the hosted model graded its
    own output.
    """

    def test_one_generator_is_accepted(self, script, monkeypatch, tmp_path):
        answers = _answers(tmp_path, [_row("r1", "qwen3:8b"), _row("r2", "qwen3:8b")])
        out = tmp_path / "report.json"
        _run(script, monkeypatch, tmp_path,
             answers=answers, judgments=tmp_path / "j.jsonl", out=out)
        assert json.loads(out.read_text())["judging"]["generation"]["model"] == "qwen3:8b"

    def test_structured_rows_without_a_generator_are_not_a_mix(
        self, script, monkeypatch, tmp_path
    ):
        # The structured route calls no model, so its None is absence of a
        # generator rather than a second one.
        answers = _answers(tmp_path, [
            _row("r1", "qwen3:8b"), _row("r2", None, route="structured"),
        ])
        out = tmp_path / "report.json"
        _run(script, monkeypatch, tmp_path,
             answers=answers, judgments=tmp_path / "j.jsonl", out=out)
        assert json.loads(out.read_text())["judging"]["generation"]["model"] == "qwen3:8b"

    def test_two_generators_stop_the_run_and_name_both(
        self, script, monkeypatch, tmp_path
    ):
        answers = _answers(tmp_path, [
            _row("r1", "qwen3:8b"), _row("r2", "gemini-flash-latest"),
        ])
        out = tmp_path / "report.json"
        with pytest.raises(SystemExit) as excinfo:
            _run(script, monkeypatch, tmp_path,
                 answers=answers, judgments=tmp_path / "j.jsonl", out=out)
        message = str(excinfo.value)
        assert "qwen3:8b" in message and "gemini-flash-latest" in message
        assert not out.exists()


class TestReportRegressionGuardIsWiredIn:
    """The script the guard's own error message recommends must itself be
    guarded, or the regression simply moves to the recommended path."""

    def test_losing_the_judgments_file_does_not_erase_the_report(
        self, script, monkeypatch, tmp_path
    ):
        answers = _answers(tmp_path, [_row("r1", "qwen3:8b")])
        out = tmp_path / "report.json"
        good = json.dumps({"judged_answers": 14, "split": "all"}, indent=2)
        out.write_text(good)

        # --judgments points at a file that does not exist, the rotated-or-lost case.
        with pytest.raises(SystemExit):
            _run(script, monkeypatch, tmp_path,
                 answers=answers, judgments=tmp_path / "gone.jsonl", out=out)

        assert out.read_text() == good

    def test_a_run_carrying_verdicts_still_writes(self, script, monkeypatch, tmp_path):
        answers = _answers(tmp_path, [_row("r1", "qwen3:8b")])
        judgments = tmp_path / "j.jsonl"
        judgments.write_text(json.dumps({
            "eval_id": "r1",
            "judge": {"total_claims": 2, "supported_claims": 2,
                      "support_rate": 1.0, "unsupported": []},
        }) + "\n")
        out = tmp_path / "report.json"
        out.write_text(json.dumps({"judged_answers": 0, "split": "all"}))

        _run(script, monkeypatch, tmp_path,
             answers=answers, judgments=judgments, out=out)

        assert json.loads(out.read_text())["judged_answers"] == 1
