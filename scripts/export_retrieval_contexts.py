"""
Export retrieval contexts for the eval set, so answers can be generated on a
machine that has no search index.

The groundedness eval needs two things per question: the passages the
retriever found, and an answer generated from them. Retrieval needs
OpenSearch and two transformer models; generation needs a GPU and thousands
of unmetered model calls. Those live on different machines here, so the step
is split and this file is the seam between them.

Routing is resolved here rather than deferred, because the structured route
answers without a model at all — an exact XBRL value with the accession
number that reported it. Shipping those to a generating machine would invite
it to paraphrase a figure that is already exact, which can only introduce
error (and is the reason ``pipeline.answer`` does not call a model on that
path either).

    python scripts/export_retrieval_contexts.py

Writes data/generation/retrieval_contexts.jsonl — commit and push it; the
GPU machine pulls it, generates, and pushes answers back.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.pipeline import DueDiligencePipeline  # noqa: E402

logger = logging.getLogger("export-contexts")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", default="data/eval_set.jsonl")
    parser.add_argument("--out", default="data/generation/retrieval_contexts.jsonl")
    parser.add_argument("--k", type=int, default=6, help="passages per question")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-rerank", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("opensearch").setLevel(logging.WARNING)

    entries = [
        json.loads(line)
        for line in Path(args.eval_set).read_text().splitlines()
        if line.strip()
    ]
    if args.limit:
        entries = entries[: args.limit]

    # Generation off: this process only routes and retrieves. Turning it on
    # would spend the hosted quota this whole split exists to avoid.
    pipeline = DueDiligencePipeline(
        enable_rerank=not args.no_rerank, enable_generation=False
    )

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)

    routes: Counter = Counter()
    started = time.perf_counter()

    with output.open("w") as handle:
        for index, entry in enumerate(entries, start=1):
            result = pipeline.answer(entry["question"], k=args.k)
            routes[result["route"]] += 1

            handle.write(json.dumps({
                "eval_id": entry["eval_id"],
                "question": entry["question"],
                "route": result["route"],
                "routing_reasons": result["routing_reasons"],
                # Present only on the structured route, where the answer is
                # already exact and needs no model.
                "structured_answer": result["answer"] if result["route"] == "structured" else None,
                "structured_fact": result["structured_fact"],
                "citations": result["citations"] if result["route"] == "structured" else [],
                "passages": result["passages"],
                "retrieval_latency_ms": result["latency_ms"],
            }) + "\n")

            if index % 20 == 0:
                logger.info("%d/%d questions", index, len(entries))

    elapsed = time.perf_counter() - started
    print(f"\nexported {len(entries)} questions in {elapsed:.0f}s")
    print(f"  routes: {dict(routes)}")
    print(f"  semantic questions needing generation: {routes['semantic']}")
    print(f"\nwrote {output}")
    print("commit and push this, then run generate_answers_locally.py on the GPU machine")


if __name__ == "__main__":
    main()
