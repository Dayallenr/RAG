"""Moving the fine-tuned checkpoint between the two machines.

The weights are 130MB of gitignored derived data produced on a CUDA box, and
everything that consumes them runs on the machine holding OpenSearch. The Hub
is the courier. None of that can be exercised against the real service here, so
these tests drive the seams either side of the network call: what gets selected
for upload, what the manifest claims, and whether a corrupted or substituted
download is caught.

**The manifest is the point.** `results/training/report.json` records no
checkpoint identity — not a path, not a hash — so losses and weights are
otherwise unrelated files that merely sit near each other. The manifest travels
by git while the weights travel by Hub, which is what makes it evidence rather
than a restatement of whatever arrived.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "transfer_checkpoint.py"


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("transfer_checkpoint", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def checkpoint(tmp_path):
    """A directory shaped like what `model.save_pretrained` writes."""
    directory = tmp_path / "bge-small-duediligence"
    (directory / "1_Pooling").mkdir(parents=True)
    (directory / "config.json").write_text('{"hidden_size": 384}')
    (directory / "modules.json").write_text("[]")
    (directory / "model.safetensors").write_bytes(b"weights" * 100)
    (directory / "1_Pooling" / "config.json").write_text('{"pooling_mode_cls_token": true}')
    return directory


@pytest.fixture
def report(tmp_path):
    path = tmp_path / "report.json"
    path.write_text(json.dumps({"device": "cuda", "final_eval_loss": 0.5198092460632324}))
    return path


class TestWhatGetsTransferred:
    def test_it_finds_the_nested_pooling_config(self, script, checkpoint):
        """A bi-encoder without its pooling module loads as a bare transformer
        and silently produces different vectors."""
        assert "1_Pooling/config.json" in script.checkpoint_files(checkpoint)

    def test_it_skips_the_trainers_output_directory(self, script, checkpoint):
        """`checkpoints/` is the trainer's `output_dir`, inside the checkpoint
        directory. Empty under `save_strategy="no"`, but an interrupted run
        fills it with optimiser state that is useless here and far larger than
        the weights."""
        (checkpoint / "checkpoints").mkdir()
        (checkpoint / "checkpoints" / "optimizer.pt").write_bytes(b"x" * 10)

        assert not any(f.startswith("checkpoints") for f in script.checkpoint_files(checkpoint))

    def test_it_skips_the_downloaders_own_bookkeeping(self, script, checkpoint):
        """`snapshot_download` writes `.cache/huggingface` into the target after
        the manifest was written. Counting it would fail every single pull."""
        cache = checkpoint / ".cache" / "huggingface"
        cache.mkdir(parents=True)
        (cache / "download_metadata").write_text("{}")

        assert not any(".cache" in f for f in script.checkpoint_files(checkpoint))


class TestItRefusesTheWrongDirectory:
    def test_a_real_checkpoint_is_accepted(self, script, checkpoint):
        assert script.looks_like_a_checkpoint(checkpoint) is True

    def test_a_directory_with_no_weights_is_not(self, script, checkpoint):
        """`models/_smoke` on this Mac is exactly this shape — a leftover
        directory with no weights in it."""
        (checkpoint / "model.safetensors").unlink()
        assert script.looks_like_a_checkpoint(checkpoint) is False

    def test_a_missing_directory_is_not(self, script, tmp_path):
        assert script.looks_like_a_checkpoint(tmp_path / "absent") is False


class TestTheManifest:
    def test_it_ties_the_weights_to_the_run_that_produced_them(
        self, script, checkpoint, report
    ):
        manifest = script.build_manifest(
            checkpoint, repo_id="u/m", private=True, revision="abc123", report_path=report
        )
        assert manifest["trained_on"] == "cuda"
        assert manifest["final_eval_loss"] == 0.5198092460632324
        assert manifest["revision"] == "abc123"

    def test_it_digests_every_transferred_file(self, script, checkpoint, report):
        manifest = script.build_manifest(
            checkpoint, repo_id="u/m", private=True, revision=None, report_path=report
        )
        assert sorted(manifest["files"]) == sorted(script.checkpoint_files(checkpoint))

    def test_a_missing_training_report_leaves_provenance_null_and_warns(
        self, script, checkpoint, tmp_path, caplog
    ):
        manifest = script.build_manifest(
            checkpoint, repo_id="u/m", private=True, revision=None,
            report_path=tmp_path / "absent.json",
        )
        assert manifest["trained_on"] is None
        assert "missing" in caplog.text


class TestVerification:
    def _manifest(self, script, checkpoint, report):
        return script.build_manifest(
            checkpoint, repo_id="u/m", private=True, revision=None, report_path=report
        )

    def test_an_intact_transfer_has_no_problems(self, script, checkpoint, report):
        assert script.verify_against_manifest(checkpoint, self._manifest(script, checkpoint, report)) == []

    def test_a_single_changed_byte_is_caught(self, script, checkpoint, report):
        manifest = self._manifest(script, checkpoint, report)
        (checkpoint / "model.safetensors").write_bytes(b"weights" * 99 + b"weightX")

        problems = script.verify_against_manifest(checkpoint, manifest)
        assert any("model.safetensors" in p and "digest mismatch" in p for p in problems)

    def test_a_truncated_transfer_is_caught(self, script, checkpoint, report):
        manifest = self._manifest(script, checkpoint, report)
        (checkpoint / "1_Pooling" / "config.json").unlink()

        assert any("missing" in p for p in script.verify_against_manifest(checkpoint, manifest))

    def test_a_file_nobody_sent_is_caught(self, script, checkpoint, report):
        """A pull into a directory that already held a different checkpoint
        leaves both mixed together."""
        manifest = self._manifest(script, checkpoint, report)
        (checkpoint / "stowaway.bin").write_bytes(b"?")

        assert any("stowaway.bin" in p for p in script.verify_against_manifest(checkpoint, manifest))


class FakeApi:
    def __init__(self):
        self.created = None
        self.uploaded = None

    def create_repo(self, repo_id, **kwargs):
        self.created = {"repo_id": repo_id, **kwargs}

    def upload_folder(self, **kwargs):
        self.uploaded = kwargs
        return type("Commit", (), {"oid": "deadbeef"})()


class TestPush:
    def _args(self, script, argv):
        return script.build_parser().parse_args(argv)

    def test_the_repository_is_private_unless_asked_otherwise(
        self, script, checkpoint, report, tmp_path
    ):
        """#25 decided against a published checkpoint. Moving a file is not
        publishing it, and the default must not quietly reverse that."""
        api = FakeApi()
        args = self._args(script, [
            "push", "--repo-id", "u/m", "--checkpoint", str(checkpoint),
            "--manifest", str(tmp_path / "manifest.json"), "--report", str(report),
        ])

        assert script.push(args, api=api) == 0
        assert api.created["private"] is True
        assert json.loads((tmp_path / "manifest.json").read_text())["private"] is True

    def test_public_is_an_explicit_choice(self, script, checkpoint, report, tmp_path):
        api = FakeApi()
        args = self._args(script, [
            "push", "--repo-id", "u/m", "--checkpoint", str(checkpoint),
            "--manifest", str(tmp_path / "manifest.json"), "--report", str(report),
            "--public",
        ])

        assert script.push(args, api=api) == 0
        assert api.created["private"] is False

    def test_the_trainers_output_directory_is_excluded_from_the_upload(
        self, script, checkpoint, report, tmp_path
    ):
        """Asserted against what reaches `upload_folder`, not against the
        constant: the ignore list existing proves nothing if it is not passed."""
        api = FakeApi()
        args = self._args(script, [
            "push", "--repo-id", "u/m", "--checkpoint", str(checkpoint),
            "--manifest", str(tmp_path / "manifest.json"), "--report", str(report),
        ])
        script.push(args, api=api)

        assert any("checkpoints" in pattern for pattern in api.uploaded["ignore_patterns"])

    def test_it_refuses_a_directory_that_is_not_a_checkpoint(
        self, script, tmp_path, report
    ):
        api = FakeApi()
        args = self._args(script, [
            "push", "--repo-id", "u/m", "--checkpoint", str(tmp_path / "nothing"),
            "--manifest", str(tmp_path / "manifest.json"), "--report", str(report),
        ])

        assert script.push(args, api=api) == 1
        assert api.created is None


class TestPull:
    def _args(self, script, argv):
        return script.build_parser().parse_args(argv)

    def test_a_verified_download_succeeds(self, script, checkpoint, report, tmp_path):
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(script.build_manifest(
            checkpoint, repo_id="u/m", private=True, revision=None, report_path=report,
        )))
        args = self._args(script, [
            "pull", "--repo-id", "u/m", "--checkpoint", str(checkpoint),
            "--manifest", str(manifest_path),
        ])

        assert script.pull(args, download=lambda **kwargs: None) == 0

    def test_a_corrupted_download_fails(self, script, checkpoint, report, tmp_path):
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(script.build_manifest(
            checkpoint, repo_id="u/m", private=True, revision=None, report_path=report,
        )))
        args = self._args(script, [
            "pull", "--repo-id", "u/m", "--checkpoint", str(checkpoint),
            "--manifest", str(manifest_path),
        ])

        def corrupt(**kwargs):
            (checkpoint / "model.safetensors").write_bytes(b"tampered")

        assert script.pull(args, download=corrupt) == 1

    def test_no_manifest_is_a_failure_not_a_pass(self, script, checkpoint, tmp_path):
        """Exiting zero here would report unverified weights as verified — and
        these weights decide every retrieval number that follows."""
        args = self._args(script, [
            "pull", "--repo-id", "u/m", "--checkpoint", str(checkpoint),
            "--manifest", str(tmp_path / "absent.json"),
        ])

        assert script.pull(args, download=lambda **kwargs: None) == 1


class TestManifestWithoutTheHub:
    """The Hub is a courier, and a courier is not always needed.

    When the weights have already reached the serving machine by some other
    route, the only thing still missing is the digest manifest — and that is
    computable from the checkpoint on the training machine with no upload,
    no token, and no repository. The evidence is identical either way: the
    digests are taken from the trained files on the machine that trained them
    and travel by git, which is what ties them to the losses in the training
    report. What is lost is only the ability to re-download, which is why the
    manifest records no repo and says so rather than leaving a null that
    reads like a failed upload.
    """

    def test_it_writes_a_manifest_with_no_repository_and_no_token(
        self, script, checkpoint, report, tmp_path
    ):
        out = tmp_path / "checkpoint.json"
        args = argparse.Namespace(
            checkpoint=str(checkpoint), manifest=str(out), report=str(report)
        )
        assert script.manifest(args) == 0
        written = json.loads(out.read_text())
        assert written["repo_id"] is None
        assert written["transport"] == "out-of-band"

    def test_the_digests_match_what_the_hub_path_would_have_written(
        self, script, checkpoint, report, tmp_path
    ):
        out = tmp_path / "checkpoint.json"
        script.manifest(argparse.Namespace(
            checkpoint=str(checkpoint), manifest=str(out), report=str(report)
        ))
        local = json.loads(out.read_text())
        hosted = script.build_manifest(
            checkpoint, repo_id="u/m", private=True, revision=None, report_path=report
        )
        assert local["files"] == hosted["files"]

    def test_it_carries_the_same_provenance_as_the_hub_path(
        self, script, checkpoint, report, tmp_path
    ):
        out = tmp_path / "checkpoint.json"
        script.manifest(argparse.Namespace(
            checkpoint=str(checkpoint), manifest=str(out), report=str(report)
        ))
        written = json.loads(out.read_text())
        assert written["trained_on"] == "cuda"
        assert written["final_eval_loss"] == 0.5198092460632324

    def test_it_refuses_a_directory_that_is_not_a_checkpoint(
        self, script, report, tmp_path
    ):
        (tmp_path / "empty").mkdir()
        out = tmp_path / "checkpoint.json"
        code = script.manifest(argparse.Namespace(
            checkpoint=str(tmp_path / "empty"), manifest=str(out), report=str(report)
        ))
        assert code == 1
        assert not out.exists()


class TestVerifyLocalWeights:
    """The serving side of the out-of-band route.

    ``pull`` verifies weights it just downloaded. When the weights arrived by
    another channel there is nothing to download, but the same check still
    has to run — and it has to fail loudly when the manifest is absent, since
    "nothing to compare against" is exactly the state that would otherwise be
    reported as verified.
    """

    def _manifest_file(self, script, checkpoint, report, tmp_path):
        path = tmp_path / "checkpoint.json"
        script.manifest(argparse.Namespace(
            checkpoint=str(checkpoint), manifest=str(path), report=str(report)
        ))
        return path

    def test_weights_matching_the_committed_manifest_verify(
        self, script, checkpoint, report, tmp_path
    ):
        path = self._manifest_file(script, checkpoint, report, tmp_path)
        assert script.verify(argparse.Namespace(
            checkpoint=str(checkpoint), manifest=str(path)
        )) == 0

    def test_a_changed_weight_file_fails(self, script, checkpoint, report, tmp_path):
        path = self._manifest_file(script, checkpoint, report, tmp_path)
        (checkpoint / "model.safetensors").write_bytes(b"different")
        assert script.verify(argparse.Namespace(
            checkpoint=str(checkpoint), manifest=str(path)
        )) == 1

    def test_a_missing_manifest_fails_rather_than_passing_vacuously(
        self, script, checkpoint, tmp_path
    ):
        assert script.verify(argparse.Namespace(
            checkpoint=str(checkpoint), manifest=str(tmp_path / "absent.json")
        )) == 1
