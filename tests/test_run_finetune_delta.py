"""The delta script's checkpoint check.

`_checkpoint_problems` decides whether the fine-tune delta report may say the
weights are tied to the training run that reported the losses. Getting it wrong
in the permissive direction is the worst failure available here: a report that
claims a verified provenance nobody verified is more misleading than one that
admits it has none, because it looks checked.

Three states, deliberately distinct — `None` for never asked, `[]` for asked
and clean, a non-empty list for asked and failed. Only `[]` is a tie.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_finetune_delta.py"


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("run_finetune_delta", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def checkpoint(tmp_path):
    directory = tmp_path / "bge-small-duediligence"
    (directory / "1_Pooling").mkdir(parents=True)
    (directory / "config.json").write_text('{"hidden_size": 384}')
    (directory / "modules.json").write_text("[]")
    (directory / "model.safetensors").write_bytes(b"weights" * 100)
    (directory / "1_Pooling" / "config.json").write_text('{"pooling_mode_cls_token": true}')
    return directory


@pytest.fixture
def manifest(checkpoint):
    from duediligence.train.checkpoint import checkpoint_files, digest

    return {
        "files": {name: digest(checkpoint / name) for name in checkpoint_files(checkpoint)}
    }


def _run(model: str | None) -> dict:
    return {"index": "duediligence-chunks-finetuned", "embedding_model": model}


class TestCheckpointProblems:
    def test_matching_weights_are_an_empty_list_not_none(self, script, checkpoint, manifest):
        """`[]` is the only value the report treats as a tie, so a clean check
        must not be reported the same way as a check that never ran."""
        assert script._checkpoint_problems(manifest, _run(str(checkpoint))) == []

    def test_a_changed_weight_file_is_reported(self, script, checkpoint, manifest):
        (checkpoint / "model.safetensors").write_bytes(b"something else entirely")

        problems = script._checkpoint_problems(manifest, _run(str(checkpoint)))
        assert problems and any("model.safetensors" in p for p in problems)

    def test_no_manifest_is_not_checked(self, script, checkpoint):
        assert script._checkpoint_problems(None, _run(str(checkpoint))) is None

    def test_a_hub_id_rather_than_a_local_path_is_not_checked(self, script, manifest):
        """The fine-tuned arm may name a model this machine never held a copy
        of. Nothing to digest is `None`, never a clean bill of health."""
        assert script._checkpoint_problems(manifest, _run("BAAI/bge-small-en-v1.5")) is None

    def test_a_run_naming_no_model_is_not_checked(self, script, manifest):
        assert script._checkpoint_problems(manifest, _run(None)) is None

    def test_it_digests_the_model_the_arm_actually_used(
        self, script, checkpoint, manifest, tmp_path
    ):
        """Not a constant path. Pointing the profile at different weights must
        change the answer, or the check keeps certifying the wrong directory.
        """
        other = tmp_path / "some-other-checkpoint"
        (other / "1_Pooling").mkdir(parents=True)
        for name in ("config.json", "modules.json", "model.safetensors"):
            (other / name).write_bytes(b"different")
        (other / "1_Pooling" / "config.json").write_bytes(b"different")

        assert script._checkpoint_problems(manifest, _run(str(checkpoint))) == []
        assert script._checkpoint_problems(manifest, _run(str(other))) != []


class TestTheRealManifestStillDescribesTheRealCheckpoint:
    """A guard on the committed artifacts themselves, skipped where they are
    absent (the weights are gitignored, so CI has no checkpoint to check)."""

    def test_the_committed_manifest_covers_the_weights_file(self):
        path = Path("results/training/checkpoint.json")
        if not path.is_file():
            pytest.skip("no committed checkpoint manifest on this machine")
        files = json.loads(path.read_text())["files"]
        normalised = {name.replace("\\", "/") for name in files}
        assert "model.safetensors" in normalised
        assert {"1_Pooling/config.json", "2_Normalize/config.json"} <= normalised
