"""
Generate synthetic training queries from the corpus using a local model.

Runs standalone: it needs the chunk files (tracked in git) and an Ollama
server, and nothing else — no OpenSearch, no index, no embeddings. That is
deliberate, so this can run on a machine with a GPU while the search index
stays on the machine that has it.

    python scripts/generate_synthetic_queries.py --limit 50      # smoke test
    python scripts/generate_synthetic_queries.py                 # full run

Resumable: completed chunks are skipped on re-run, so an interrupted run
costs nothing. Output is one JSON object per (query, chunk) pair.

The contamination guard runs on every pair — chunks the eval set is labelled
against are excluded up front, and generated queries too close to an eval
question are dropped. See duediligence/train/synthetic.py.
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.generate.ollama_backend import OllamaBackend  # noqa: E402
from duediligence.train.synthetic import (  # noqa: E402
    MIN_CHUNK_CHARS,
    build_prompt,
    eval_chunk_ids,
    is_contaminated,
    normalize_question,
    parse_questions,
)

logger = logging.getLogger("synthetic")


def load_chunks(directories: list[str], *, excluded: set[str]) -> list[dict]:
    """Every usable chunk, with eval-labelled and too-short ones removed."""
    chunks, skipped_short, skipped_eval = [], 0, 0
    for directory in directories:
        for path in sorted(Path(directory).glob("*.jsonl")):
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                chunk = json.loads(line)
                if chunk.get("chunk_id") in excluded:
                    skipped_eval += 1
                    continue
                if len(chunk.get("text", "")) < MIN_CHUNK_CHARS:
                    skipped_short += 1
                    continue
                chunks.append(chunk)
    logger.info(
        "%d usable chunks (skipped %d eval-labelled, %d too short)",
        len(chunks), skipped_eval, skipped_short,
    )
    return chunks


def stratified_sample(chunks: list[dict], target: int, *, seed: int = 13) -> list[dict]:
    """Sample evenly across (company, chunk_type) rather than uniformly.

    A uniform sample would be dominated by paragraphs, which outnumber
    tables three to one — and tables are exactly where dense retrieval is
    weakest (recall@10 0.18 vs BM25's 0.43), so they are the stratum the
    fine-tuning most needs represented.
    """
    if target >= len(chunks):
        return chunks

    buckets: dict[tuple, list[dict]] = {}
    for chunk in chunks:
        buckets.setdefault(
            (chunk.get("company"), chunk.get("chunk_type")), []
        ).append(chunk)

    rng = random.Random(seed)
    for bucket in buckets.values():
        rng.shuffle(bucket)

    sampled: list[dict] = []
    while len(sampled) < target:
        progressed = False
        for bucket in buckets.values():
            if bucket and len(sampled) < target:
                sampled.append(bucket.pop())
                progressed = True
        if not progressed:
            break
    return sampled


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="data/training/synthetic_queries.jsonl")
    parser.add_argument("--eval-set", default="data/eval_set.jsonl")
    parser.add_argument("--chunk-dirs", nargs="+", default=["data/chunks", "data/tables"])
    parser.add_argument("--chunks", type=int, default=1600, help="chunks to generate from")
    parser.add_argument("--per-chunk", type=int, default=3, help="questions per chunk")
    parser.add_argument("--limit", type=int, default=None, help="stop after N new chunks")
    parser.add_argument("--model", default="qwen3:8b")
    parser.add_argument("--host", default=None, help="Ollama host (default: env or localhost)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    backend = OllamaBackend(args.model, host=args.host)
    if not backend.available():
        raise SystemExit(
            f"Ollama is not serving {args.model!r} at {backend.host}.\n"
            f"  Start it, then:  ollama pull {args.model}"
        )
    logger.info("using %s at %s", args.model, backend.host)

    excluded = eval_chunk_ids(args.eval_set)
    logger.info("contamination guard: %d eval-labelled chunks excluded", len(excluded))

    eval_questions = [
        normalize_question(json.loads(line)["question"])
        for line in Path(args.eval_set).read_text().splitlines()
        if line.strip()
    ]

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    done = {
        json.loads(line)["chunk_id"]
        for line in (output.read_text().splitlines() if output.exists() else [])
        if line.strip()
    }
    if done:
        logger.info("resuming: %d chunks already generated", len(done))

    pool = [c for c in load_chunks(args.chunk_dirs, excluded=excluded)
            if c["chunk_id"] not in done]
    selected = stratified_sample(pool, args.chunks - len(done))
    if args.limit:
        selected = selected[: args.limit]

    logger.info("generating from %d chunks", len(selected))

    written, dropped = 0, 0
    by_type: Counter = Counter()
    with output.open("a") as handle:
        for index, chunk in enumerate(selected, start=1):
            try:
                raw = backend.generate(build_prompt(chunk, n=args.per_chunk))
            except Exception as error:  # noqa: BLE001 - never lose completed work
                logger.error("stopping at chunk %d: %s", index, error)
                break

            for question in parse_questions(raw, max_questions=args.per_chunk):
                if is_contaminated(question, eval_questions):
                    dropped += 1
                    logger.warning("dropped (too close to an eval question): %s", question[:80])
                    continue
                handle.write(json.dumps({
                    "query": question,
                    "chunk_id": chunk["chunk_id"],
                    "company": chunk.get("company"),
                    "chunk_type": chunk.get("chunk_type"),
                    "filing_type": chunk.get("filing_type"),
                    "generated_by": args.model,
                }) + "\n")
                written += 1
                by_type[chunk.get("chunk_type")] += 1
            handle.flush()

            if index % 25 == 0:
                logger.info("%d/%d chunks, %d queries written", index, len(selected), written)

    print(f"\nqueries written this run: {written}")
    print(f"dropped as contaminated:  {dropped}")
    print(f"by chunk type: {dict(by_type)}")
    total = sum(1 for line in output.read_text().splitlines() if line.strip())
    print(f"total in {output}: {total}")


if __name__ == "__main__":
    main()
