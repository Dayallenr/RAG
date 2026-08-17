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
from duediligence.train.synthetic import normalize_question  # noqa: E402

logger = logging.getLogger("finetune")


def load_split(path: str) -> list[dict]:
    return [
        json.loads(line)
        for line in Path(path).read_text().splitlines()
        if line.strip()
    ]


def assert_no_eval_leakage(rows: list[dict], eval_set: str) -> None:
    """Refuse to train if any eval question reached the training data.

    The last line of defence. The guard already ran at generation and again
    after company-name normalisation, but this is the point of no return: a
    contaminated run produces a number that looks like an improvement and
    is not one, and nothing downstream would reveal it.
    """
    eval_questions = {
        normalize_question(json.loads(line)["question"])
        for line in Path(eval_set).read_text().splitlines()
        if line.strip()
    }
    train_questions = {normalize_question(r["query"]) for r in rows}
    overlap = eval_questions & train_questions
    if overlap:
        raise SystemExit(
            f"ABORTING: {len(overlap)} eval questions appear verbatim in the training "
            "data. The reported delta would measure memorisation, not retrieval."
        )
    logger.info("contamination check passed: no eval question in %d training rows", len(rows))


def main() -> None:
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
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    from datasets import Dataset
    from sentence_transformers import (
        SentenceTransformer,
        SentenceTransformerTrainer,
        SentenceTransformerTrainingArguments,
    )
    from sentence_transformers.losses import MultipleNegativesRankingLoss

    train_rows = load_split(args.train)
    val_rows = load_split(args.val)
    assert_no_eval_leakage(train_rows + val_rows, args.eval_set)

    device = resolve_device()
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

    training_args = SentenceTransformerTrainingArguments(
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
        report_to=["wandb"] if _wandb_enabled() else [],
        run_name="finetune-bge-small",
        seed=17,
        # fp16 is a CUDA path; MPS runs fp32 and enabling it here silently
        # does nothing on this machine.
        fp16=False,
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
