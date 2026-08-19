"""Digesting a sentence-transformers checkpoint, and checking one against a manifest.

`results/training/report.json` records losses and hyperparameters but no
checkpoint identity — not a path, not a hash. The digest manifest is the only
thing joining those losses to the weights that got indexed, so it is written on
the machine that trained them and travels by git while the weights travel by
some other channel.

This lives in the package rather than in `scripts/transfer_checkpoint.py`
because two callers need the same answer: the transfer script, which verifies
what arrived, and the fine-tune delta report, which must not describe weights
as tied to a training run without that check having actually run. A second
implementation of "does this file still hash to what was claimed" is exactly
the kind of drift that lets a report certify itself.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

#: The trainer's own ``output_dir`` sits inside the checkpoint directory. With
#: ``save_strategy="no"`` it holds nothing, but an interrupted or differently
#: configured run would fill it with optimiser state that is useless to a
#: serving machine and far larger than the weights.
TRAINER_OUTPUT_DIR = "checkpoints"


def checkpoint_files(directory: Path) -> list[str]:
    """Every file that makes up the checkpoint, relative to its directory.

    Names are POSIX whatever wrote them. The manifest is written on a Windows
    CUDA box and read on a Mac, so ``str(relative)`` would key the nested
    pooling and normalize configs as ``1_Pooling\\config.json`` and no reader
    on another platform could match them.

    Dot-directories are skipped: ``snapshot_download`` writes its own
    ``.cache/huggingface`` bookkeeping into the target, and verifying that
    against a manifest written before it existed would fail every pull.
    """
    files = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(directory)
        parts = relative.parts
        if parts[0] == TRAINER_OUTPUT_DIR or any(part.startswith(".") for part in parts):
            continue
        files.append(relative.as_posix())
    return files


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def verify_against_manifest(directory: Path, manifest: dict) -> list[str]:
    """Problems with what arrived. Empty means the weights are the ones sent.

    Manifest keys are re-normalised on the way in, not merely on the way out:
    a manifest written before ``checkpoint_files`` used POSIX names still
    carries Windows separators and must keep verifying.
    """
    expected = {
        name.replace("\\", "/"): want
        for name, want in (manifest.get("files") or {}).items()
    }
    problems = []
    for name, want in sorted(expected.items()):
        path = directory / name
        if not path.exists():
            problems.append(f"missing: {name}")
        elif (got := digest(path)) != want:
            problems.append(f"digest mismatch: {name} (expected {want[:12]}…, got {got[:12]}…)")
    for name in checkpoint_files(directory):
        if name not in expected:
            problems.append(f"unexpected file not in the manifest: {name}")
    return problems
