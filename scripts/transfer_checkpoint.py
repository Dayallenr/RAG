"""
Move the fine-tuned checkpoint between the training machine and this one.

The fine-tune runs on a CUDA box (ADR 0005) and everything downstream — the
index, the delta, serving — runs on the Mac that holds OpenSearch. The two are
on different subnets, so the weights have to travel. `/models/` is gitignored
and 130MB of derived weights do not belong in this repository's history, so
git is not the channel.

**The Hub repository is private by default.** #25 decided against a published
checkpoint, and moving a file is not publishing it. `--public` reverses that
decision deliberately rather than by accident; if you pass it, say so on #25,
because the card's claims change with it.

**A manifest travels by git, not with the weights.** `push` writes
`results/training/checkpoint.json` — the digest of every uploaded file, the
Hub revision, and the eval loss from the training report — and that file is
committed. `pull` verifies what arrived against it. A manifest shipped
alongside the weights would be signed by the same corruption it is supposed to
catch, and a manifest carried by an independent channel is also the only thing
that ties these weights to the run that produced them: `results/training/
report.json` records no checkpoint identity at all, so "the checkpoint" and
"the losses" are otherwise two unrelated artifacts.

Usage, on the training machine:

    export HF_TOKEN=hf_...
    python scripts/transfer_checkpoint.py push --repo-id <user>/bge-small-duediligence
    git add results/training/checkpoint.json && git commit && git push

then here:

    git pull
    export HF_TOKEN=hf_...
    python scripts/transfer_checkpoint.py pull --repo-id <user>/bge-small-duediligence
    DUEDILIGENCE_CONFIG_PROFILE=finetuned python scripts/build_index.py --recreate
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logger = logging.getLogger("transfer-checkpoint")

DEFAULT_CHECKPOINT = "models/bge-small-duediligence"
DEFAULT_MANIFEST = "results/training/checkpoint.json"
TRAINING_REPORT = "results/training/report.json"

# The trainer's own output_dir sits inside the checkpoint directory. With
# save_strategy="no" it holds nothing, but an interrupted or differently
# configured run would fill it with optimiser state that is useless here and
# far larger than the weights.
IGNORED = ("checkpoints/*", "checkpoints/**")

# What sentence-transformers writes and what the embedder needs back. Checked
# before the upload so a wrong --checkpoint fails on this machine rather than
# after 130MB have crossed the network.
REQUIRED_FILES = ("config.json", "modules.json")
WEIGHT_FILES = ("model.safetensors", "pytorch_model.bin")


def checkpoint_files(directory: Path) -> list[str]:
    """Every file to transfer, relative to the checkpoint directory.

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
        if parts[0] == "checkpoints" or any(part.startswith(".") for part in parts):
            continue
        files.append(str(relative))
    return files


def looks_like_a_checkpoint(directory: Path) -> bool:
    if not directory.is_dir():
        return False
    if not all((directory / name).exists() for name in REQUIRED_FILES):
        return False
    return any((directory / name).exists() for name in WEIGHT_FILES)


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def build_manifest(directory: Path, *, repo_id: str, private: bool, revision: str | None,
                   report_path: Path) -> dict:
    """Describe exactly what was uploaded, and which run it came from."""
    files = checkpoint_files(directory)
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    if not report:
        logger.warning(
            "%s is missing — the manifest cannot say which run these weights came from",
            report_path,
        )
    return {
        "repo_id": repo_id,
        "private": private,
        "revision": revision,
        "uploaded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "total_bytes": sum((directory / name).stat().st_size for name in files),
        # Provenance, not measurement: these two are what tie the weights to
        # results/training/report.json, which records no checkpoint identity.
        "trained_on": report.get("device"),
        "final_eval_loss": report.get("final_eval_loss"),
        "files": {name: digest(directory / name) for name in files},
    }


def verify_against_manifest(directory: Path, manifest: dict) -> list[str]:
    """Problems with what arrived. Empty means the weights are the ones sent."""
    expected = manifest.get("files") or {}
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


def resolve_token(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    from dotenv import load_dotenv

    load_dotenv()
    return os.environ.get("HF_TOKEN") or None


def push(args, *, api=None) -> int:
    directory = Path(args.checkpoint)
    if not looks_like_a_checkpoint(directory):
        print(
            f"{directory} is not a sentence-transformers checkpoint "
            f"(need {', '.join(REQUIRED_FILES)} and one of {', '.join(WEIGHT_FILES)})",
            file=sys.stderr,
        )
        return 1

    if api is None:
        from huggingface_hub import HfApi

        api = HfApi()

    token = resolve_token(args.token)
    private = not args.public
    api.create_repo(args.repo_id, token=token, private=private, exist_ok=True)
    result = api.upload_folder(
        repo_id=args.repo_id,
        folder_path=str(directory),
        token=token,
        ignore_patterns=list(IGNORED),
        commit_message="Upload the fine-tuned bi-encoder checkpoint",
    )

    manifest = build_manifest(
        directory,
        repo_id=args.repo_id,
        private=private,
        revision=getattr(result, "oid", None),
        report_path=Path(args.report),
    )
    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    visibility = "private" if private else "PUBLIC"
    print(f"uploaded {len(manifest['files'])} files "
          f"({manifest['total_bytes'] / 1e6:.1f} MB) to {args.repo_id} [{visibility}]")
    print(f"wrote {manifest_path} — commit it, or the pull side verifies nothing")
    return 0


def pull(args, *, download=None) -> int:
    if download is None:
        from huggingface_hub import snapshot_download

        download = snapshot_download

    directory = Path(args.checkpoint)
    download(
        repo_id=args.repo_id,
        local_dir=str(directory),
        token=resolve_token(args.token),
        revision=args.revision,
    )

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(
            f"downloaded to {directory}, but {manifest_path} is not here so nothing was "
            "verified. Commit the manifest on the training machine and pull it, or these "
            "weights are untraceable to any run.",
            file=sys.stderr,
        )
        return 1

    problems = verify_against_manifest(directory, json.loads(manifest_path.read_text()))
    if problems:
        print(f"{directory} does not match {manifest_path}:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text())
    print(f"verified {len(manifest['files'])} files against {manifest_path}")
    print(f"  trained on {manifest.get('trained_on')}, "
          f"final eval loss {manifest.get('final_eval_loss')}")
    print("\nnext: DUEDILIGENCE_CONFIG_PROFILE=finetuned python scripts/build_index.py --recreate")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("push", "pull"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--repo-id", required=True, help="e.g. <user>/bge-small-duediligence")
        sub.add_argument("--checkpoint", default=DEFAULT_CHECKPOINT)
        sub.add_argument("--manifest", default=DEFAULT_MANIFEST)
        sub.add_argument("--token", default=None, help="defaults to HF_TOKEN in the environment or .env")

    push_parser = subparsers.choices["push"]
    push_parser.add_argument("--report", default=TRAINING_REPORT)
    push_parser.add_argument(
        "--public", action="store_true",
        help="publish the weights publicly, reversing #25's no-hosted-checkpoint "
             "decision — say so on that ticket if you use it",
    )
    subparsers.choices["pull"].add_argument("--revision", default=None)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    raise SystemExit(push(args) if args.command == "push" else pull(args))


if __name__ == "__main__":
    main()
