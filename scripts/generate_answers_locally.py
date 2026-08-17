"""
Generate answers for the eval set from exported retrieval contexts.

Runs on the GPU machine. Needs only ``requests`` and an Ollama server — no
OpenSearch, no embedding model, no index. Retrieval already happened on the
machine that has those; this reads what it produced.

    python scripts/generate_answers_locally.py --limit 5    # smoke test
    python scripts/generate_answers_locally.py              # all of them

Structured-route questions are passed through untouched. Their answer is an
exact XBRL figure with the accession number that reported it, and running an
exact number through a language model to have it restated can only introduce
error.

Resumable: completed questions are skipped, so an interrupt costs nothing.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.generate.answer import generate_answer  # noqa: E402
from duediligence.generate.ollama_backend import OllamaBackend  # noqa: E402

logger = logging.getLogger("generate-local")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contexts", default="data/generation/retrieval_contexts.jsonl")
    parser.add_argument("--out", default="results/generation/answers.jsonl")
    parser.add_argument("--model", default="qwen3:8b")
    parser.add_argument("--host", default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    contexts_path = Path(args.contexts)
    if not contexts_path.exists():
        raise SystemExit(
            f"{contexts_path} not found. It is produced on the machine holding the "
            "search index by scripts/export_retrieval_contexts.py, then committed "
            "and pushed. Pull the latest main and try again."
        )

    backend = OllamaBackend(args.model, host=args.host)
    if not backend.available():
        raise SystemExit(
            f"Ollama is not serving {args.model!r} at {backend.host}.\n"
            f"  Start it, then:  ollama pull {args.model}"
        )
    logger.info("using %s at %s", args.model, backend.host)

    rows = [
        json.loads(line)
        for line in contexts_path.read_text().splitlines()
        if line.strip()
    ]

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    done = {
        json.loads(line)["eval_id"]
        for line in (output.read_text().splitlines() if output.exists() else [])
        if line.strip()
    }
    if done:
        logger.info("resuming: %d answers already generated", len(done))

    pending = [r for r in rows if r["eval_id"] not in done]
    if args.limit:
        pending = pending[: args.limit]
    logger.info("%d questions to answer", len(pending))

    counts: Counter = Counter()
    with output.open("a") as handle:
        for index, row in enumerate(pending, start=1):
            if row["route"] == "structured":
                # No model call: the figure is already exact.
                record = {
                    "eval_id": row["eval_id"],
                    "question": row["question"],
                    "route": "structured",
                    "answer": row["structured_answer"],
                    "refused": False,
                    "citations": row["citations"],
                    "n_passages": 0,
                    "passage_chunk_ids": [],
                    "generated_by": None,
                }
                counts["structured"] += 1
            else:
                try:
                    generated = generate_answer(
                        row["question"], row["passages"], backend=backend
                    )
                except Exception as error:  # noqa: BLE001 - never lose finished work
                    logger.error("stopping at %s: %s", row["eval_id"], error)
                    break
                record = {
                    "eval_id": row["eval_id"],
                    "question": row["question"],
                    "route": "semantic",
                    "answer": generated.answer,
                    "refused": generated.refused,
                    "citations": generated.citations,
                    "n_passages": len(row["passages"]),
                    "passage_chunk_ids": [p.get("chunk_id") for p in row["passages"]],
                    "generated_by": backend.model,
                }
                counts["semantic"] += 1
                counts["refused"] += int(generated.refused)
                counts["cited"] += int(bool(generated.citations))

            handle.write(json.dumps(record) + "\n")
            handle.flush()

            if index % 10 == 0:
                logger.info("%d/%d answered", index, len(pending))

    print(f"\nanswered this run: {counts['semantic'] + counts['structured']}")
    print(f"  semantic (model-generated): {counts['semantic']}")
    print(f"  structured (no model call): {counts['structured']}")
    print(f"  refusals: {counts['refused']}   with citations: {counts['cited']}")
    total = sum(1 for line in output.read_text().splitlines() if line.strip())
    print(f"\ntotal in {output}: {total}")
    print("commit and push this file; judging runs on the machine with the hosted key")


if __name__ == "__main__":
    main()
