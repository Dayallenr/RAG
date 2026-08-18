"""
Sample candidate chunks to draft retrieval eval questions from.

This does not write questions — it surfaces a diverse, information-dense
slice of the corpus to read and write questions against, so the eval set is
grounded in text someone actually looked at rather than generated from the
corpus statistics.

Stratified across company x filing_type x chunk_type so the eval set can't
end up accidentally measuring "retrieval on COLB 10-K risk factors" and
calling it corpus-wide performance. Within each stratum it prefers chunks
that are *specific* — containing dollar figures, dates, percentages, or
proper nouns — because a question written against boilerplate ("the Company
is subject to various legal proceedings") has no unique answer and would
make the ground truth arbitrary.

Usage:
    python scripts/sample_eval_candidates.py --per-stratum 2 --seed 20240811
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.index.enrich import enrich_placeholder_chunks
from duediligence.index.opensearch_client import iter_jsonl_chunks

_CHUNK_SOURCES = ("data/chunks", "data/tables", "data/chunks_charts")

# Signals that a chunk states something specific enough to ask about.
_DOLLARS_RE = re.compile(r"\$\s?[\d,]+(?:\.\d+)?\s*(?:million|billion|thousand)?", re.IGNORECASE)
_PERCENT_RE = re.compile(r"\d+(?:\.\d+)?\s?%")
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")

_MIN_CHARS = 300
_MAX_CHARS = 2500


def specificity_score(text: str) -> int:
    """How much concrete, askable detail a chunk contains."""
    return (
        2 * len(_DOLLARS_RE.findall(text))
        + 2 * len(_PERCENT_RE.findall(text))
        + len(_YEAR_RE.findall(text))
    )


def load_corpus() -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for directory in _CHUNK_SOURCES:
        for path in sorted(Path(directory).glob("*.jsonl")):
            chunks.extend(enrich_placeholder_chunks(list(iter_jsonl_chunks([path]))))
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-stratum", type=int, default=2, help="candidates per stratum")
    parser.add_argument("--seed", type=int, default=20240811, help="RNG seed (reproducibility)")
    parser.add_argument("--out", default=None, help="write JSONL here instead of stdout")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    strata: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)

    for chunk in load_corpus():
        text = chunk["text"].strip()
        if not (_MIN_CHARS <= len(text) <= _MAX_CHARS):
            continue
        if chunk["chunk_type"] == "section" and not chunk.get("enriched"):
            continue
        strata[(chunk["company"], chunk["filing_type"], chunk["chunk_type"])].append(chunk)

    selected: list[dict[str, Any]] = []
    for key in sorted(strata):
        candidates = strata[key]
        # Sample from the most specific half, then shuffle — taking a strict
        # top-N would return near-identical dense financial tables.
        candidates.sort(key=lambda c: specificity_score(c["text"]), reverse=True)
        pool = candidates[: max(args.per_stratum * 10, 20)]
        rng.shuffle(pool)
        selected.extend(pool[: args.per_stratum])

    lines = [
        json.dumps(
            {
                "chunk_id": c["chunk_id"],
                "company": c["company"],
                "filing_type": c["filing_type"],
                "filing_date": c["filing_date"],
                "chunk_type": c["chunk_type"],
                "section": c["section"],
                "source_url": c["source_url"],
                "text": c["text"],
            }
        )
        for c in selected
    ]

    if args.out:
        Path(args.out).write_text("\n".join(lines) + "\n")
        print(f"wrote {len(lines)} candidates across {len(strata)} strata to {args.out}")
    else:
        print("\n".join(lines))


if __name__ == "__main__":
    main()
