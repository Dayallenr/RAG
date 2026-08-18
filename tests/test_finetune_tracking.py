"""Whether the fine-tuning run reaches the experiment tracker anyone can read.

#11 trained on the RTX 5070 on 2026-08-18 and produced
`results/training/report.json`, but an anonymous read of the public project
found thirteen runs and **none of them from training**. The cause was wiring,
not a missing key: the script handed `report_to=["wandb"]` to the Hugging Face
trainer and never set `WANDB_PROJECT`, and that callback defaults to a project
called `"huggingface"` — so a run with a key set would have logged somewhere
`scripts/verify_wandb_runs.py` does not look, and a run without one logged
nowhere. Neither case failed.

These tests guard the two seams that let that happen silently:

- the payload's run name matches the name `RUN_REPORTS` looks for, so the
  verifier and the logger cannot drift apart;
- the logged metrics are exactly `flatten_metrics` of the report, which is what
  `compare_run` demands — it fails a run with a single extra or missing key.

**What they do not guard**: the one line at the end of a real training run that
calls `log_training_run`. That path needs a GPU and 27MB of untracked splits,
so it cannot run here. `--log-report-only` drives the same function through
`main()`, which is why the logging lives in a function rather than inline.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from duediligence.track import flatten_metrics
from duediligence.track.verify import RUN_REPORTS

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "finetune_biencoder.py"
REPORT = "results/training/report.json"


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("finetune_biencoder", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def sample_report():
    return {
        "base_model": "BAAI/bge-small-en-v1.5",
        "train_triplets": 12758,
        "val_triplets": 1429,
        "epochs": 1.0,
        "batch_size": 32,
        "learning_rate": 2e-05,
        "device": "cuda",
        "fp16": True,
        "gradient_checkpointing": False,
        "train_seconds": 121.0,
        "final_train_loss": 0.5379423904418945,
        "final_eval_loss": 0.5198092460632324,
        "log_history": [{"loss": 1.76, "step": 25}, {"eval_loss": 0.52, "step": 399}],
    }


class TestTheVerifierAndTheLoggerAgree:
    def test_the_training_report_is_registered_for_verification(self):
        """Unregistered, a missing training run is indistinguishable from a
        healthy project: `verify_wandb_runs.py` only checks names it knows."""
        assert RUN_REPORTS["training"] == REPORT

    def test_the_script_and_the_verifier_name_the_same_report(self, script):
        """Ties the two constants together rather than to a literal. Comparing
        `RUN_REPORTS["training"]` against a path typed into this file leaves the
        script free to write somewhere else: change `DEFAULT_REPORT` and every
        test stays green while `verify_wandb_runs.py` exits 1 on a missing
        report."""
        assert RUN_REPORTS[script.RUN_NAME] == script.DEFAULT_REPORT

    def test_the_run_name_is_the_one_the_verifier_looks_for(self, script, sample_report):
        payload = script.build_training_run_payload(sample_report)
        assert payload["name"] in RUN_REPORTS


class TestThePayload:
    def test_metrics_are_exactly_the_flattened_report(self, script, sample_report):
        """`compare_run` fails on one extra or one missing key, so anything but
        equality here turns a correct run into a red verification."""
        payload = script.build_training_run_payload(sample_report)
        assert payload["metrics"] == flatten_metrics(sample_report)

    def test_the_config_records_the_device_that_trained(self, script, sample_report):
        """The run happened on another machine. A hosted run that does not say
        so invites the reader to assume it ran where the repository lives."""
        assert script.build_training_run_payload(sample_report)["config"]["device"] == "cuda"


class TestLogReportOnly:
    def _run(self, script, monkeypatch, argv):
        monkeypatch.setattr(sys, "argv", ["finetune_biencoder.py", *argv])

        def refuse(*args, **kwargs):
            raise AssertionError("the report-only path must not build a training run")

        monkeypatch.setattr(script, "build_training_arguments", refuse)
        with pytest.raises(SystemExit) as exit_info:
            script.main()
        return exit_info.value.code

    def _report(self, tmp_path, payload):
        path = tmp_path / "report.json"
        path.write_text(json.dumps(payload))
        return str(path)

    def test_it_logs_the_report_on_disk_without_training(
        self, script, monkeypatch, tmp_path, sample_report
    ):
        captured = {}

        def fake_log_run(**kwargs):
            captured.update(kwargs)
            return "https://wandb.ai/e/p/runs/abc"

        monkeypatch.setattr(script, "tracking_enabled", lambda: True)
        monkeypatch.setattr(script, "log_run", fake_log_run)
        report = self._report(tmp_path, sample_report)

        assert self._run(script, monkeypatch, ["--log-report-only", "--report", report]) == 0
        assert captured["name"] == "training"
        assert captured["metrics"]["final_eval_loss"] == sample_report["final_eval_loss"]

    def test_it_fails_when_tracking_is_off(
        self, script, monkeypatch, tmp_path, sample_report
    ):
        """Exiting zero here would report a run as tracked when nothing left the
        machine — the same silent no-op that lost the original training run."""
        monkeypatch.setattr(script, "tracking_enabled", lambda: False)
        monkeypatch.setattr(
            script, "log_run", lambda **kwargs: pytest.fail("nothing should be logged")
        )
        report = self._report(tmp_path, sample_report)

        assert self._run(script, monkeypatch, ["--log-report-only", "--report", report]) == 1

    def test_tracking_on_with_no_url_is_reported_as_its_own_case(
        self, script, monkeypatch, tmp_path, sample_report, capsys
    ):
        """`log_run` returns None both when tracking is off and when a run was
        created but exposed no URL. Those need opposite advice: re-running the
        second publishes a duplicate rather than replacing it."""
        monkeypatch.setattr(script, "tracking_enabled", lambda: True)
        monkeypatch.setattr(script, "log_run", lambda **kwargs: None)
        report = self._report(tmp_path, sample_report)

        assert self._run(script, monkeypatch, ["--log-report-only", "--report", report]) == 1
        assert "duplicate" in capsys.readouterr().err

    def test_it_refuses_a_report_that_is_not_a_training_report(
        self, script, monkeypatch, tmp_path
    ):
        monkeypatch.setattr(
            script, "log_run", lambda **kwargs: pytest.fail("nothing should be logged")
        )
        report = self._report(tmp_path, {"queries": 101, "index": "chunks"})

        assert self._run(script, monkeypatch, ["--log-report-only", "--report", report]) == 1

    def test_it_fails_when_there_is_no_report_to_log(self, script, monkeypatch, tmp_path):
        monkeypatch.setattr(
            script, "log_run", lambda **kwargs: pytest.fail("nothing should be logged")
        )
        missing = tmp_path / "absent.json"

        assert self._run(script, monkeypatch, ["--log-report-only", "--report", str(missing)]) == 1


class TestOnlyTheRunOfRecordIsPublished:
    """A hosted run named `training` replaces its predecessor rather than adding
    to it — `latest_finished_runs` cites the newest finished run of each name.
    So a five-step smoke run with a key in `.env` would become the published
    evidence for the fine-tune while `results/training/report.json` still held
    the real one, and verification would flip to 107 mismatches against a
    hosted run nobody can retract."""

    def _args(self, script, argv):
        return script.build_parser().parse_args(argv)

    def test_a_full_run_writing_the_registered_report_is_published(self, script):
        assert script.is_the_run_of_record(self._args(script, [])) is True

    def test_a_step_capped_run_is_not(self, script):
        assert script.is_the_run_of_record(self._args(script, ["--max-steps", "5"])) is False

    def test_a_run_writing_somewhere_else_is_not(self, script):
        """The hosted summary has to mirror the report `RUN_REPORTS` maps the
        name to, or the verifier is comparing two different runs."""
        args = self._args(script, ["--report", "/tmp/scratch.json"])
        assert script.is_the_run_of_record(args) is False


class TestItRefusesToPublishTheWrongFile:
    """A hosted run cannot be retracted, so wrong input is caught before the
    network call. Logging `results/retrieval/report.json` under the name
    `training` would fail verification permanently: 534 metrics only on the
    hosted run, 107 missing from it."""

    def test_a_training_report_is_recognised(self, script, sample_report):
        assert script.looks_like_a_training_report(sample_report) is True

    def test_another_report_is_not(self, script):
        assert script.looks_like_a_training_report({"queries": 101, "index": "chunks"}) is False

    def test_json_that_is_not_an_object_is_not(self, script):
        """`report.get(...)` would raise AttributeError on a list, after the
        file had already been read and accepted."""
        assert script.looks_like_a_training_report([1, 2, 3]) is False
