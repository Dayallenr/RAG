"""
Build fine-tuning triplets from synthetic queries by mining hard negatives.

For each synthetic query, run the *current* retriever and keep the top hits
that are not the passage the query was generated from. Those are the
passages the retriever confuses with the right answer today, which is where
the headroom is. Random negatives would be trivially separable and teach
almost nothing.

Writes data/training/train.jsonl and data/training/val.jsonl, split by query
so no query straddles the boundary.

    python scripts/mine_hard_negatives.py
    python scripts/mine_hard_negatives.py --limit 200   # quick pass
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

from duediligence.config import load_config  # noqa: E402
from duediligence.index.embed import ChunkEmbedder  # noqa: E402
from duediligence.index.hybrid_search import hybrid_search  # noqa: E402
from duediligence.index.opensearch_client import build_client  # noqa: E402
from duediligence.train.mine import (  # noqa: E402
    normalize_company_names,
    select_negatives,
    split_by_query,
)
from duediligence.train.synthetic import (  # noqa: E402
    eval_chunk_ids,
    is_contaminated,
    normalize_question,
)

logger = logging.getLogger("mine")

_BATCH = 256


def fetch_texts(client, index_name: str, chunk_ids: set[str]) -> dict[str, str]:
    """Chunk text for every id we need, in batches."""
    texts: dict[str, str] = {}
    ids = sorted(chunk_ids)
    for start in range(0, len(ids), _BATCH):
        batch = ids[start : start + _BATCH]
        response = client.mget(index=index_name, body={"ids": batch}, _source=["text"])
        for doc in response.get("docs", []):
            if doc.get("found"):
                texts[doc["_id"]] = doc["_source"].get("text", "")
    return texts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", default="data/training/synthetic_queries.jsonl")
    parser.add_argument("--eval-set", default="data/eval_set.jsonl")
    parser.add_argument("--out-dir", default="data/training")
    parser.add_argument("--negatives", type=int, default=3, help="hard negatives per query")
    parser.add_argument("--skip-top", type=int, default=1,
                        help="drop the N hardest hits (likely near-duplicates)")
    parser.add_argument("--candidates", type=int, default=20)
    parser.add_argument("--val-fraction", type=float, default=0.1)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("opensearch").setLevel(logging.WARNING)

    rows = [
        json.loads(line)
        for line in Path(args.queries).read_text().splitlines()
        if line.strip()
    ]
    if args.limit:
        rows = rows[: args.limit]
    logger.info("%d synthetic queries", len(rows))

    # Normalise the ticker-as-company-name artifact before anything else, so
    # the queries we mine against are the ones we will train on.
    renamed = 0
    for row in rows:
        normalized = normalize_company_names(row["query"])
        if normalized != row["query"]:
            renamed += 1
        row["query"] = normalized
    logger.info("normalised company names in %d queries", renamed)

    # Re-run the contamination guard after renaming: normalisation moves
    # queries closer to the eval set's vocabulary, so a pair that was clear
    # before could cross the threshold now.
    eval_norm = [
        normalize_question(json.loads(line)["question"])
        for line in Path(args.eval_set).read_text().splitlines()
        if line.strip()
    ]
    excluded_chunks = eval_chunk_ids(args.eval_set)
    before = len(rows)
    rows = [
        r for r in rows
        if r["chunk_id"] not in excluded_chunks and not is_contaminated(r["query"], eval_norm)
    ]
    logger.info("contamination guard after renaming: dropped %d, kept %d", before - len(rows), len(rows))

    config = load_config()
    client = build_client(config.opensearch)
    index_name = config.opensearch.index_name
    embedder = ChunkEmbedder(config.models.embedding_model)

    logger.info("embedding %d queries", len(rows))
    vectors = embedder.embed_queries([r["query"] for r in rows])

    triplets: list[dict] = []
    needed: set[str] = set()
    no_negatives = 0
    started = time.perf_counter()

    for index, (row, vector) in enumerate(zip(rows, vectors, strict=True), start=1):
        hits = hybrid_search(
            client, index_name, row["query"], vector.tolist(),
            k=args.candidates, candidate_k=args.candidates,
        )
        negatives = select_negatives(
            [h["chunk_id"] for h in hits], row["chunk_id"],
            n=args.negatives, skip_top=args.skip_top,
        )
        if not negatives:
            no_negatives += 1
            continue

        needed.add(row["chunk_id"])
        needed.update(negatives)
        for negative in negatives:
            triplets.append({
                "query": row["query"],
                "positive_chunk_id": row["chunk_id"],
                "negative_chunk_id": negative,
                "company": row.get("company"),
                "chunk_type": row.get("chunk_type"),
            })

        if index % 500 == 0:
            logger.info("%d/%d queries mined", index, len(rows))

    logger.info("fetching text for %d chunks", len(needed))
    texts = fetch_texts(client, index_name, needed)

    complete = []
    for triplet in triplets:
        positive = texts.get(triplet["positive_chunk_id"], "")
        negative = texts.get(triplet["negative_chunk_id"], "")
        if positive and negative:
            complete.append(triplet | {"positive": positive, "negative": negative})

    train, validation = split_by_query(complete, val_fraction=args.val_fraction)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, split in (("train", train), ("val", validation)):
        with (out / f"{name}.jsonl").open("w") as handle:
            for triplet in split:
                handle.write(json.dumps(triplet) + "\n")

    elapsed = time.perf_counter() - started
    print(f"\nmined in {elapsed:.0f}s")
    print(f"  triplets: {len(complete)}  (train {len(train)}, val {len(validation)})")
    print(f"  distinct queries: {len({t['query'] for t in complete})}")
    print(f"  queries with no usable negative: {no_negatives}")
    print(f"  by chunk type: {dict(Counter(t['chunk_type'] for t in complete))}")
    print(f"\nwrote {out}/train.jsonl and {out}/val.jsonl")


if __name__ == "__main__":
    main()
