"""
The fine-tune delta — the number the whole training path exists for.

Runs the **four-run matrix**: the off-the-shelf bi-encoder and the fine-tuned
one, each with and without the cross-encoder, over the same eval set with the
same code, differing only by config profile and rerank setting. Then it
subtracts them into ``results/finetune_delta/report.json``.

Four runs rather than two, because the two obvious shortcuts are both
misleading. The cross-encoder re-scores the top candidates and is the largest
single quality jump in the pipeline, so a bi-encoder that genuinely improved
dense retrieval can show a null delta *after* reranking — it merely reordered
within a pool the reranker was about to reorder anyway. Report only that pair
and a real improvement disappears; report only the unreranked pair and the
figure overstates what a user of the served system would actually experience.

The headline is the **held-out test split**. The fusion weight and the rerank
depth were both selected by sweeping against dev, so a delta reported on the
full set would be a number optimised against twice. Dev and full-set figures
are written beside it, each labelled with the split that produced it.

Each arm is run in its own subprocess. This is an 8 GB machine that already
swaps, and two embedding models plus a cross-encoder resident at once is how
the last index build degraded from 80 chunks/s to 3 — a fresh process per run
hands the memory back in between.

Usage:
    # the whole matrix, then the comparison (about a minute of retrieval,
    # plus model load; run it with nothing else heavy on the box)
    python scripts/run_finetune_delta.py

    # recompute the comparison from reports that already exist
    python scripts/run_finetune_delta.py --from-reports
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.config import PROFILE_ENV_VAR
from duediligence.eval.eval_set import DEFAULT_EVAL_SET_PATH, SPLITS
from duediligence.eval.finetune_delta import ALL, METRICS, build_comparison
from duediligence.track import flatten_metrics, log_run
from duediligence.train.checkpoint import verify_against_manifest

logger = logging.getLogger("finetune-delta")

DEFAULT_OUT_DIR = Path("results/finetune_delta")
TRAINING_REPORT_PATH = "results/training/report.json"
POOL_REPORT_NAME = "rerank_pool.json"
CHECKPOINT_MANIFEST_PATH = "results/training/checkpoint.json"

#: The four cells: (arm, profile, rerank). ``None`` is the base config, which
#: is named as ``None`` rather than as a "base" profile so the baseline arm
#: runs the exact configuration every other report in this repository used.
CELLS = (
    ("base", None, False),
    ("base", None, True),
    ("finetuned", "finetuned", False),
    ("finetuned", "finetuned", True),
)


def report_path(out_dir: Path, arm: str, rerank: bool) -> Path:
    return out_dir / f"{arm}-{'rerank' if rerank else 'norerank'}.json"


def run_eval(
    arm: str, profile: str | None, rerank: bool, out: Path, eval_set: str,
    *, tracked: bool = True,
) -> None:
    """One cell of the matrix, in its own process.

    The profile travels as an environment variable because that is the one
    switch that changes both the embedding model and the index it is queried
    against — the config loader refuses a profile that moves one without the
    other, which is what stops a run scoring fine-tuned vectors against
    baseline ones and reporting a plausible ranking rather than an error.
    """
    command = [
        sys.executable, "-m", "duediligence.eval.run_retrieval_eval",
        "--eval-set", eval_set,
        "--out", str(out),
        "--run-name", f"finetune-delta-{arm}-{'rerank' if rerank else 'norerank'}",
    ]
    if not rerank:
        command.append("--no-rerank")

    env = dict(os.environ)
    if not tracked:
        # Same reason as the comparison run: a cell writing outside the
        # registered directory may not claim the registered run name.
        env["DUEDILIGENCE_TRACKING"] = "0"
    if profile:
        env[PROFILE_ENV_VAR] = profile
    else:
        env.pop(PROFILE_ENV_VAR, None)
    # Each cell logs under its own run name. Sharing the default name would
    # point the tracker's report check at results/retrieval/report.json, which
    # a run against the fine-tuned index did not write.

    logger.info("running %s arm, rerank=%s -> %s", arm, rerank, out)
    subprocess.run(command, check=True, env=env)


def load_report(path: Path) -> dict:
    report = json.loads(path.read_text())
    # Recorded so the comparison names the file each cell came from; a report
    # that cannot say which run produced it is a report two runs can be
    # confused in.
    report["report_path"] = str(path)
    return report


def _optional_json(path: str) -> dict | None:
    file = Path(path)
    return json.loads(file.read_text()) if file.is_file() else None


def _print_table(report: dict) -> None:
    headline = report["headline"]
    print(
        f"\n=== fine-tune delta, {headline['split']} split "
        f"({headline['queries']} questions, "
        f"{headline['human_verified_queries']} human-verified) ==="
    )
    header = f"{'retriever':<16}{'CE':>4}" + "".join(f"{m:>12}" for m in METRICS)
    print(header)
    print("-" * len(header))
    for name, payload in headline["retrievers"].items():
        flag = "yes" if payload["cross_encoder"] else "no"
        print(f"{name + ' base':<16}{flag:>4}"
              + "".join(f"{payload['base'][m]:>12.3f}" for m in METRICS))
        print(f"{name + ' tuned':<16}{flag:>4}"
              + "".join(f"{payload['finetuned'][m]:>12.3f}" for m in METRICS))
        print(f"{name + ' delta':<16}{'':>4}"
              + "".join(f"{payload['delta'][m]:>+12.3f}" for m in METRICS))
        print()

    print("dense recall@10 by chunk type (base -> tuned, delta):")
    for group, values in headline["by_chunk_type"]["dense"].items():
        print(f"  {group:<20} {values['base']['recall@10']:.3f} -> "
              f"{values['finetuned']['recall@10']:.3f}  "
              f"({values['delta']['recall@10']:+.3f}, n={values['queries']})")

    print("\ndense recall@10 by question type (base -> tuned, delta):")
    for group, values in headline["by_question_type"]["dense"].items():
        print(f"  {group:<20} {values['base']['recall@10']:.3f} -> "
              f"{values['finetuned']['recall@10']:.3f}  "
              f"({values['delta']['recall@10']:+.3f}, n={values['queries']})")

    print("\nother splits (dense / hybrid_rerank recall@10 delta):")
    for split, payload in report["splits"].items():
        dense = payload["retrievers"]["dense"]["delta"]["recall@10"]
        reranked = payload["retrievers"]["hybrid_rerank"]["delta"]["recall@10"]
        print(f"  {split:<6} n={payload['queries']:<4} dense {dense:+.3f}   "
              f"hybrid+rerank {reranked:+.3f}")


def _checkpoint_problems(manifest: dict | None, finetuned_run: dict) -> list[str] | None:
    """Whether the weights on this machine are the ones the manifest describes.

    ``None`` means the question was not asked — no manifest, or no local
    checkpoint directory to ask it about. It is deliberately distinct from
    ``[]``, which means the digests were compared and matched: the report
    treats only the empty list as a tie to the training run, so a manifest that
    exists but was never checked cannot certify itself.

    The directory comes from the fine-tuned run's own ``embedding_model``
    rather than from a constant here, so what gets digested is the model that
    arm actually queried with. A constant would keep reporting a clean verify
    after the profile was pointed somewhere else.
    """
    # `not manifest.get("files")` rather than `not manifest`, to match the
    # report's own presence test. A manifest that lost its file map is absent
    # as far as both are concerned, and disagreeing about that put
    # `checkpoint_manifest_present: false` next to a populated problem list.
    model = finetuned_run.get("embedding_model")
    if not manifest or not manifest.get("files") or not model:
        return None
    directory = Path(model)
    if not directory.is_dir():
        # A Hub id rather than a local path: nothing on this disk to digest.
        return None
    return verify_against_manifest(directory, manifest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", default=DEFAULT_EVAL_SET_PATH)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument(
        "--from-reports",
        action="store_true",
        help="skip the four runs and recompute the comparison from existing reports",
    )
    parser.add_argument("--headline-split", choices=[*SPLITS, ALL], default="test")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # The tracker run names below are fixed strings, and duediligence/track/
    # verify.py maps each of them to a file under the default directory. A run
    # writing elsewhere may not claim them: the hosted metrics would be diffed
    # against reports this run did not write, and both would still look
    # internally consistent — the same hazard guard_profiled_output covers in
    # the retrieval eval. Writing elsewhere stays available; only the logging
    # is withheld.
    tracked = out_dir == DEFAULT_OUT_DIR
    if not tracked:
        logger.info(
            "--out-dir is %s, not %s: skipping experiment tracking, because the "
            "run names are registered against the default directory",
            out_dir, DEFAULT_OUT_DIR,
        )

    for arm, profile, rerank in CELLS:
        path = report_path(out_dir, arm, rerank)
        if args.from_reports:
            if not path.is_file():
                parser.error(f"--from-reports but {path} does not exist")
            continue
        run_eval(arm, profile, rerank, path, args.eval_set, tracked=tracked)

    runs = {
        arm: {
            "no_rerank": load_report(report_path(out_dir, arm, False)),
            "rerank": load_report(report_path(out_dir, arm, True)),
        }
        for arm in ("base", "finetuned")
    }

    # Read once, then checked against the weights — the report distinguishes
    # "no manifest" from "manifest that does not match", and only an actual
    # digest comparison can tell those apart.
    checkpoint_manifest = _optional_json(CHECKPOINT_MANIFEST_PATH)

    report = build_comparison(
        base_runs=runs["base"],
        finetuned_runs=runs["finetuned"],
        training_report=_optional_json(TRAINING_REPORT_PATH),
        training_report_path=TRAINING_REPORT_PATH,
        checkpoint_manifest=checkpoint_manifest,
        checkpoint_problems=_checkpoint_problems(
            checkpoint_manifest, runs["finetuned"]["no_rerank"]
        ),
        # Why the reranked cell moved or did not: written by
        # scripts/verify_rerank_pool.py, folded in when it exists and recorded
        # as absent when it does not, rather than explained in prose here.
        pool_report=_optional_json(str(out_dir / POOL_REPORT_NAME)),
        headline_split=args.headline_split,
    )

    output = out_dir / "report.json"
    output.write_text(json.dumps(report, indent=2) + "\n")

    run_url = None if not tracked else log_run(
        name="finetune-delta",
        tags=["retrieval", "eval", "finetune"],
        config={
            "eval_set": report["eval_set"],
            "headline_split": report["headline_split"],
            "base_index": report["arms"]["base"]["index"],
            "base_embedding_model": report["arms"]["base"]["embedding_model"],
            "finetuned_index": report["arms"]["finetuned"]["index"],
            "finetuned_embedding_model": report["arms"]["finetuned"]["embedding_model"],
            "reranker_model": report["arms"]["finetuned"]["reranker_model"],
            "queries": report["headline"]["queries"],
            "human_verified_queries": report["headline"]["human_verified_queries"],
            "weights_traceable_to_training_run": (
                report["training_run"] or {}
            ).get("weights_traceable_to_this_run"),
        },
        # ``per_query`` is not in this report at all — the comparison is the
        # artifact, and the four run reports beside it keep the raw rows.
        metrics=flatten_metrics(report),
    )

    _print_table(report)
    absorption = report["rerank_absorption"]
    if absorption["reranked_lists_identical"]:
        print(f"\nNOTE: the cross-encoder returned identical result lists on all "
              f"{absorption['queries']} questions in both arms.")
        pool = absorption["candidate_pool"]
        if pool:
            print(f"      {pool['finding']}")
        else:
            print("      Run scripts/verify_rerank_pool.py to see whether it was "
                  "handed the same candidates in both arms.")

    if not report["consistency"]["bm25_identical_across_arms"]:
        print("\nWARNING: BM25 moved between the two arms. Same text, same "
              "analyzer — it should not. These arms are not comparable.")
    training = report["training_run"]
    if training and not training["weights_traceable_to_this_run"]:
        print(f"\nNOTE: {training['traceability_note']}")
    if run_url:
        print(f"\ntracked: {run_url}")
    print(f"\nwrote {output}")


if __name__ == "__main__":
    main()
