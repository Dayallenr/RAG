"""
Fine-tune the bi-encoder on mined triplets.

This is the project's first and only training run. Everything else is
inference: this is where a loss actually gets minimised.

**The query instruction prefix must be applied here exactly as it is at
inference.** BGE is asymmetric — queries carry
"Represent this sentence for searching relevant passages: " and passages do
not (see ``index/embed.py``). Training anchors without it while embedding
queries with it at serving time is a train/serve skew that does not raise an
error anywhere: the model trains fine, the eval runs fine, and retrieval is
quietly worse than the baseline for a reason no metric points at. The prefix
is applied to every anchor below for that reason.

**MultipleNegativesRankingLoss with explicit hard negatives.** Each row is
(anchor, positive, negative). The loss treats every other in-batch passage
as an additional negative, so effective negatives per anchor scale with
batch size — which is why batch size matters more here than it does for a
classifier, and why it is the first thing to raise if the GPU allows.

**Validation is measured on held-out queries, never held-out rows.** One
query produces several triplets; splitting by row would leak. See
``train/mine.py::split_by_query``.

The 101 human-written eval questions appear in neither split. They are the
test set, and the delta against them is the only number this run is for.

**This does not fit on the 8 GB Mac, measured rather than assumed.** Passages
run to the model's full 512-token window (6.8% of mined positives exceed it,
and ``ChunkEmbedder`` never lowers ``max_seq_length``, so shortening sequences
here would be a train/serve skew of the same class as dropping the prefix).
At 512 tokens the attention activations dominate: batch 32 and batch 16 both
die with an MPS out-of-memory, and batch 8 survives only by swapping, at
roughly 710 s/step — about 13 days for one epoch. ``--gradient-checkpointing``
is wired up because activation memory is the binding constraint and trading
compute for it is the standard fix, but it has never been run at the corpus's
real sequence length or on a GPU — only proved to train on a toy batch. Train on the CUDA box (ADR 0005); this script picks the device
itself, so nothing here needs changing to do that.

**The run is logged through this repository's own ``log_run``, not through the
trainer's callback.** Hugging Face's wandb integration takes its project from
``WANDB_PROJECT`` and defaults to one named "huggingface", so ``report_to``
sent this run somewhere ``scripts/verify_wandb_runs.py`` does not look — which
is how the 2026-08-18 run left no trace in the project the README links.
Logging the report instead means the hosted summary mirrors the report file key
for key, which is what the verifier diffs.

    python scripts/finetune_biencoder.py --epochs 1

A run performed on another machine travels back as its report. Log it without
retraining:

    python scripts/finetune_biencoder.py --log-report-only
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.index.embed import QUERY_INSTRUCTION, resolve_device  # noqa: E402
from duediligence.track import flatten_metrics, log_run, tracking_enabled  # noqa: E402
from duediligence.train.synthetic import (  # noqa: E402
    EvalLeakageError,
    assert_no_eval_leakage,
)

logger = logging.getLogger("finetune")

DEFAULT_REPORT = "results/training/report.json"

# The name the hosted run must carry. ``duediligence.track.verify.RUN_REPORTS``
# maps it to the report file, and a test asserts the two agree — a renamed run
# would otherwise make the verifier report a missing run rather than a rename.
RUN_NAME = "training"


def load_split(path: str) -> list[dict]:
    return [
        json.loads(line)
        for line in Path(path).read_text().splitlines()
        if line.strip()
    ]


def build_parser() -> argparse.ArgumentParser:
    """Split out from ``main`` so the flags can be tested without importing
    torch — everything below this function's return is a training run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", default="data/training/train.jsonl")
    parser.add_argument("--val", default="data/training/val.jsonl")
    parser.add_argument("--eval-set", default="data/eval_set.jsonl")
    parser.add_argument("--base-model", default="BAAI/bge-small-en-v1.5")
    parser.add_argument("--out", default="models/bge-small-duediligence")
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--warmup-ratio", type=float, default=0.1)
    parser.add_argument("--max-steps", type=int, default=-1, help="cap steps for a quick run")
    parser.add_argument(
        "--fp16", action="store_true",
        help="mixed-precision training (CUDA only; ignored with a warning elsewhere)",
    )
    parser.add_argument(
        "--gradient-checkpointing", action="store_true",
        help="recompute activations in the backward pass instead of storing them "
             "(much less memory, roughly 30%% more compute) — see the module docstring",
    )
    parser.add_argument("--report", default=DEFAULT_REPORT)
    parser.add_argument(
        "--log-report-only", action="store_true",
        help="log an existing training report to the experiment tracker and exit, "
             "training nothing — for a run performed on another machine whose "
             "report is the artifact that travelled back",
    )
    return parser


def build_training_run_payload(report: dict) -> dict:
    """What reaches ``log_run`` for a training report.

    The metrics are ``flatten_metrics`` of the report and nothing else, because
    that is exactly what ``verify.compare_run`` diffs the hosted summary
    against — it fails on a single extra or missing key, so anything added here
    would turn a correct run into a red verification. Run configuration goes in
    ``config``, where it is recorded without being mistaken for a measurement.
    """
    return {
        "name": RUN_NAME,
        "tags": ["training", "bi-encoder"],
        "config": {
            "base_model": report.get("base_model"),
            # Which machine produced these losses. The training run happens on
            # a CUDA box that is not the machine holding the index (ADR 0005),
            # and a hosted run that does not say so invites the reader to
            # assume otherwise.
            "device": report.get("device"),
            "epochs": report.get("epochs"),
            "batch_size": report.get("batch_size"),
            "learning_rate": report.get("learning_rate"),
            "fp16": report.get("fp16"),
            "gradient_checkpointing": report.get("gradient_checkpointing"),
            "train_triplets": report.get("train_triplets"),
            "val_triplets": report.get("val_triplets"),
        },
        "metrics": flatten_metrics(report),
    }


def log_training_run(report: dict) -> str | None:
    """Log one training report. Returns the run URL, or ``None`` if tracking is off."""
    return log_run(**build_training_run_payload(report))


def is_the_run_of_record(args) -> bool:
    """Should this run become the hosted run the project cites?

    ``verify.latest_finished_runs`` cites the newest *finished* run of each
    name, so a hosted run named ``training`` is not additive — it replaces the
    one the README's link resolves to. A five-step smoke run would therefore
    become the published evidence for the fine-tune while
    ``results/training/report.json`` still held the real one, and verification
    would flip to 107 mismatches with no way to retract the hosted run.

    Two things disqualify a run, both meaning "this is not the run of record":
    a step cap, which is what a quick check looks like, and a report path other
    than the one ``RUN_REPORTS`` maps the hosted name to — the hosted summary
    has to mirror *that* file or the verifier is comparing two different runs.
    """
    return args.max_steps <= 0 and args.report == DEFAULT_REPORT


def looks_like_a_training_report(payload: object) -> bool:
    """Cheap shape check before anything is published.

    Logging ``results/retrieval/report.json`` under the name ``training``
    succeeds, and then fails verification permanently: a hosted run cannot be
    retracted. Wrong input is worth catching before the network call, not
    after.
    """
    return isinstance(payload, dict) and "base_model" in payload and "final_eval_loss" in payload


def log_existing_report(path: str) -> int:
    """Log a report produced by an earlier run. Returns a process exit code."""
    report_path = Path(path)
    if not report_path.exists():
        print(f"no training report at {path} — nothing to log", file=sys.stderr)
        return 1

    payload = json.loads(report_path.read_text())
    if not looks_like_a_training_report(payload):
        print(
            f"{path} is not a training report (expected base_model and final_eval_loss) — "
            f"refusing to publish it as the run {RUN_NAME!r}, which cannot be retracted",
            file=sys.stderr,
        )
        return 1

    # Checked before the call rather than inferred from its return value: a
    # ``None`` URL means "tracking off" and "logged but no URL came back"
    # equally, and those two need opposite advice.
    if not tracking_enabled():
        print(
            f"nothing was logged for {path} — tracking is off. Set WANDB_API_KEY, and "
            "check DUEDILIGENCE_TRACKING is not set to 0.",
            file=sys.stderr,
        )
        return 1

    url = log_training_run(payload)
    if url is None:
        print(
            f"tracking is on but no run URL came back for {path}. The run may still have "
            "been created — check the project before re-running, because a second attempt "
            "publishes a duplicate rather than replacing it.",
            file=sys.stderr,
        )
        return 1
    print(f"tracked: {url}")
    return 0


def build_training_arguments(args, *, output, fp16: bool, report_to: list[str]):
    """Assemble the trainer's arguments.

    Split out from ``main`` so a test can assert that a flag actually reaches
    the trainer. Reading the flag back off ``args`` proves only that argparse
    parsed it; the failure worth guarding is the wiring in *this* function
    going missing, which trains without the setting and reports success.
    """
    from sentence_transformers import SentenceTransformerTrainingArguments

    return SentenceTransformerTrainingArguments(
        output_dir=str(output / "checkpoints"),
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        warmup_ratio=args.warmup_ratio,
        eval_strategy="steps",
        eval_steps=100,
        save_strategy="no",
        logging_steps=25,
        report_to=report_to,
        run_name="finetune-bge-small",
        seed=17,
        fp16=fp16,
        gradient_checkpointing=args.gradient_checkpointing,
    )


def main() -> None:
    args = build_parser().parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # Before the heavy imports: this path trains nothing.
    if args.log_report_only:
        raise SystemExit(log_existing_report(args.report))

    from datasets import Dataset
    from sentence_transformers import (
        SentenceTransformer,
        SentenceTransformerTrainer,
    )
    from sentence_transformers.losses import MultipleNegativesRankingLoss

    train_rows = load_split(args.train)
    val_rows = load_split(args.val)
    try:
        cleared = assert_no_eval_leakage(
            (r["query"] for r in train_rows + val_rows), args.eval_set
        )
    except EvalLeakageError as error:
        raise SystemExit(f"ABORTING: {error}") from error
    logger.info("contamination check passed over %d training rows", cleared)

    device = resolve_device()

    # fp16 is a CUDA path. On MPS or CPU the trainer would drop it silently, so
    # it is downgraded loudly here instead and the report records the value the
    # trainer actually received. The run continues: mixed precision is a speed
    # optimisation, and losing it changes how long training takes, not what it
    # produces. (Contrast the query prefix, which would change the result and
    # is therefore not optional anywhere.)
    fp16 = args.fp16
    if fp16 and device != "cuda":
        logger.warning("--fp16 ignored: mixed precision needs CUDA, running on %s", device)
        fp16 = False
    logger.info(
        "%d train / %d val triplets on %s", len(train_rows), len(val_rows), device
    )

    def to_dataset(rows: list[dict]) -> Dataset:
        return Dataset.from_dict({
            # The prefix is the whole point — see the module docstring.
            "anchor": [QUERY_INSTRUCTION + r["query"] for r in rows],
            "positive": [r["positive"] for r in rows],
            "negative": [r["negative"] for r in rows],
        })

    model = SentenceTransformer(args.base_model, device=device)
    loss = MultipleNegativesRankingLoss(model)

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)

    # No trainer-side tracking callback on purpose. Hugging Face's wandb
    # integration takes its project from ``WANDB_PROJECT`` and defaults to a
    # project literally named "huggingface", so ``report_to=["wandb"]`` sent
    # this run somewhere ``scripts/verify_wandb_runs.py`` never looks — which
    # is why the 2026-08-18 run left no trace in the project the README links.
    # The run is logged below instead, through the same ``log_run`` every other
    # report in this repository uses, so the hosted summary mirrors the report
    # file key for key and the verifier can diff the two.
    training_args = build_training_arguments(
        args, output=output, fp16=fp16, report_to=[]
    )

    trainer = SentenceTransformerTrainer(
        model=model,
        args=training_args,
        train_dataset=to_dataset(train_rows),
        eval_dataset=to_dataset(val_rows),
        loss=loss,
    )

    started = time.perf_counter()
    trainer.train()
    elapsed = time.perf_counter() - started

    model.save_pretrained(str(output))
    logger.info("saved to %s", output)

    history = [h for h in trainer.state.log_history if "loss" in h or "eval_loss" in h]
    metrics = {
        "base_model": args.base_model,
        "train_triplets": len(train_rows),
        "val_triplets": len(val_rows),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.lr,
        "device": device,
        # Read off the trainer, not off ``args``: if the wiring in
        # ``build_training_arguments`` were ever dropped, reporting the parsed
        # flag would record a setting the run did not actually use.
        "fp16": training_args.fp16,
        "gradient_checkpointing": training_args.gradient_checkpointing,
        "train_seconds": round(elapsed, 1),
        "final_train_loss": next(
            (h["loss"] for h in reversed(history) if "loss" in h), None
        ),
        "final_eval_loss": next(
            (h["eval_loss"] for h in reversed(history) if "eval_loss" in h), None
        ),
        "log_history": history,
    }
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(metrics, indent=2) + "\n")

    # A no-op without a key: the report file stays the source of truth. If this
    # is skipped, re-run with --log-report-only rather than retraining — the
    # losses are already on disk.
    if not is_the_run_of_record(args):
        logger.warning(
            "not tracked: a step cap or a non-default --report means this is not the "
            "run of record, and publishing it would replace the hosted run the README "
            "cites. Log it deliberately with --log-report-only --report %s",
            args.report,
        )
    elif run_url := log_training_run(metrics):
        print(f"\ntracked: {run_url}")
    else:
        logger.warning(
            "not tracked — run with --log-report-only --report %s once WANDB_API_KEY is set",
            args.report,
        )

    print(f"\ntrained in {elapsed / 60:.1f} min on {device}")
    print(f"  final train loss: {metrics['final_train_loss']}")
    print(f"  final eval loss:  {metrics['final_eval_loss']}")
    print(f"\nmodel: {output}")
    print(f"report: {report}")
    print("\nnext: rebuild the index with this model and re-run the retrieval eval")


if __name__ == "__main__":
    main()
