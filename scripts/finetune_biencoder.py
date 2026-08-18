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

    python scripts/finetune_biencoder.py --epochs 1
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
from duediligence.train.synthetic import (  # noqa: E402
    EvalLeakageError,
    assert_no_eval_leakage,
)

logger = logging.getLogger("finetune")


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
    return parser


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

    training_args = build_training_arguments(
        args, output=output, fp16=fp16, report_to=["wandb"] if _wandb_enabled() else []
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
    report = Path("results/training/report.json")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(metrics, indent=2) + "\n")

    print(f"\ntrained in {elapsed / 60:.1f} min on {device}")
    print(f"  final train loss: {metrics['final_train_loss']}")
    print(f"  final eval loss:  {metrics['final_eval_loss']}")
    print(f"\nmodel: {output}")
    print(f"report: {report}")
    print("\nnext: rebuild the index with this model and re-run the retrieval eval")


def _wandb_enabled() -> bool:
    from duediligence.track import tracking_enabled

    return tracking_enabled()


if __name__ == "__main__":
    main()
