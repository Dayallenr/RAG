"""
Embed every text chunk in the corpus and index it into OpenSearch.

Sources indexed (everything with prose to search):
    data/chunks/<ticker>.jsonl         narrative document/section/paragraph chunks
    data/tables/<ticker>.jsonl         serialized financial tables
    data/chunks_charts/<ticker>.jsonl  Gemini Vision chart descriptions

Deliberately **not** indexed: data/facts/<ticker>.jsonl. XBRL facts are
exact numeric values with a period and a unit — they're answered by lookup,
not by semantic similarity, which is the whole basis of the Phase 6 query
router. Embedding "NetIncomeLoss = 348700000 USD CY2023" would produce a
vector that matches badly and retrieves worse than a dictionary hit.

Idempotent: documents are keyed by the content-addressed ``chunk_id``, so
re-running overwrites rather than duplicating, and an interrupted run can
simply be repeated.

Usage:
    python scripts/build_index.py                 # index into whatever is missing
    python scripts/build_index.py --recreate      # drop and rebuild the index
    python scripts/build_index.py --limit 500     # smoke test on a small slice
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.config import load_config
from duediligence.index.embed import ChunkEmbedder
from duediligence.index.enrich import enrich_placeholder_chunks
from duediligence.index.opensearch_client import (
    build_client,
    bulk_index,
    bulk_load_settings,
    create_index,
    document_count,
    existing_chunk_ids,
    iter_jsonl_chunks,
    to_index_document,
)

logger = logging.getLogger("build_index")

_CHUNK_SOURCES = ("data/chunks", "data/tables", "data/chunks_charts")

# Embedding batch: how many chunks to encode per forward pass. Indexing
# batch is separate (in bulk_index) because the bottleneck is the GPU/MPS
# encode, not the HTTP round trip.
_EMBED_BATCH = 256

# Chunks below this are structural noise, not retrievable content — a
# handful of the corpus's chunks are bare fragments like "​" or a lone page
# number left over from the filing's layout. Indexing them can only add
# false positives to retrieval results.
_MIN_TEXT_CHARS = 20


def corpus_paths() -> list[Path]:
    paths: list[Path] = []
    for directory in _CHUNK_SOURCES:
        paths.extend(sorted(Path(directory).glob("*.jsonl")))
    return paths


def indexable_chunks(
    chunk_types: set[str] | None, skip_ids: set[str] | None = None
) -> Iterator[dict[str, Any]]:
    """Stream chunks that belong in the index, enriched and filtered.

    Reads **one source file at a time and fully**, rather than streaming the
    whole corpus lazily: enrichment rolls a section's child paragraphs up
    into it, so a section chunk can't be finalized until its children have
    been seen. One company's narrative chunks is the natural unit — self
    contained (a chunk's parent is always in the same file) and small enough
    to hold in memory (the largest is ~7.5k chunks).
    """
    for path in corpus_paths():
        chunks = enrich_placeholder_chunks(list(iter_jsonl_chunks([path])))
        for chunk in chunks:
            if chunk_types is not None and chunk["chunk_type"] not in chunk_types:
                continue
            # A section that enrichment couldn't fill stayed a bare heading —
            # a guaranteed false positive (see enrich.py), so it is not
            # embedded at all.
            if chunk["chunk_type"] == "section" and not chunk.get("enriched"):
                continue
            if len(chunk["text"].strip()) < _MIN_TEXT_CHARS:
                continue
            if skip_ids and chunk["chunk_id"] in skip_ids:
                continue
            yield chunk


def batched_chunks(
    limit: int | None,
    chunk_types: set[str] | None = None,
    skip_ids: set[str] | None = None,
    batch_size: int = _EMBED_BATCH,
) -> Iterator[list[dict[str, Any]]]:
    """Batch indexable chunks for embedding.

    ``chunk_types`` restricts the run to a subset (e.g. paragraphs only) —
    used both to index the levels independently and by Phase 5's chunking
    ablation, which needs to measure retrieval with and without each level.
    """
    batch: list[dict[str, Any]] = []
    yielded = 0
    for chunk in indexable_chunks(chunk_types, skip_ids):
        batch.append(chunk)
        yielded += 1
        if len(batch) >= batch_size:
            yield batch
            batch = []
        if limit is not None and yielded >= limit:
            break
    if batch:
        yield batch


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--recreate", action="store_true",
        help="delete and recreate the index (destructive — re-embeds everything)",
    )
    parser.add_argument("--limit", type=int, default=None, help="index at most N chunks (smoke test)")
    parser.add_argument(
        "--chunk-types", default=None,
        help="comma-separated chunk_types to index (default: all), e.g. paragraph,table",
    )
    parser.add_argument("--device", default=None, help="torch device override (mps/cuda/cpu)")
    parser.add_argument(
        "--resume", action="store_true",
        help="skip chunks already in the index (embedding is the expensive half)",
    )
    parser.add_argument(
        "--batch-size", type=int, default=_EMBED_BATCH,
        help=f"chunks per embedding pass (default {_EMBED_BATCH}; lower it on a memory-tight machine)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # These two log one line per HTTP call — hundreds of model-download
    # requests and one per bulk batch, which buries the progress output.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("opensearch").setLevel(logging.WARNING)

    config = load_config()
    client = build_client(config.opensearch)
    info = client.info()
    logger.info(
        "connected to %s %s at %s",
        info["version"]["distribution"], info["version"]["number"], config.opensearch.local_endpoint,
    )

    created = create_index(client, config.opensearch.index_name, recreate=args.recreate)
    logger.info("index %s %s", config.opensearch.index_name, "created" if created else "already exists")

    skip_ids: set[str] = set()
    if args.resume:
        skip_ids = existing_chunk_ids(client, config.opensearch.index_name)
        logger.info("resume: %d chunks already indexed, skipping them", len(skip_ids))

    embedder = ChunkEmbedder(
        config.models.embedding_model, device=args.device, batch_size=min(args.batch_size, 128)
    )

    started = time.perf_counter()
    total_indexed = 0
    total_errors = 0
    by_type = Counter()
    by_company = Counter()

    chunk_types = set(args.chunk_types.split(",")) if args.chunk_types else None
    with bulk_load_settings(client, config.opensearch.index_name):
        for batch in batched_chunks(args.limit, chunk_types, skip_ids, args.batch_size):
            embed_started = time.perf_counter()
            vectors = embedder.embed_passages(chunk["text"] for chunk in batch)
            embed_seconds = time.perf_counter() - embed_started

            actions = [
                to_index_document(chunk, vector.tolist())
                for chunk, vector in zip(batch, vectors, strict=True)
            ]
            bulk_started = time.perf_counter()
            succeeded, errors = bulk_index(client, config.opensearch.index_name, actions)
            bulk_seconds = time.perf_counter() - bulk_started

            total_indexed += succeeded
            total_errors += len(errors)
            by_type.update(chunk["chunk_type"] for chunk in batch)
            by_company.update(chunk["company"] for chunk in batch)

            if errors:
                logger.error("%d documents rejected, first: %s", len(errors), errors[0])

            elapsed = time.perf_counter() - started
            # Embed and bulk times are logged separately on purpose: when a
            # run slows down, the split immediately says whether the cost is
            # in the model or in OpenSearch, instead of requiring the whole
            # thing to be re-run under instrumentation to find out.
            logger.info(
                "indexed %d chunks (%.0f/s overall; this batch embed %.1fs + bulk %.1fs; %d errors)",
                total_indexed, total_indexed / elapsed, embed_seconds, bulk_seconds, total_errors,
            )

    elapsed = time.perf_counter() - started
    in_index = document_count(client, config.opensearch.index_name)

    print(f"\nindexed {total_indexed} chunks in {elapsed:.0f}s ({total_errors} errors)")
    print(f"index {config.opensearch.index_name} now holds {in_index} documents")
    print(f"  by type:    {dict(by_type)}")
    print(f"  by company: {dict(by_company)}")


if __name__ == "__main__":
    main()
