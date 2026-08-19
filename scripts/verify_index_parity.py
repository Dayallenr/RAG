"""Check a profile's index against the baseline it will be compared against.

#22 builds a second index with a different embedding model. Two things then
have to be true before #23's delta means anything, and neither is visible by
looking at the index:

1. **Same corpus.** A delta measured over a smaller index is measuring
   coverage, not the model. Checked exactly, by diffing the two indexes'
   ``_id`` sets — not by comparing document counts, because two indexes
   holding the same number of *different* chunks compare equal. Per-type
   counts are reported alongside because they say *where* a gap is.

2. **Its own vectors.** An index built with the wrong embedding model does not
   error. Cosine similarity across two incompatible spaces is still a number,
   so it returns plausible rankings and every downstream figure is quietly
   meaningless. This re-embeds a sample of chunks and scores each stored
   vector against both models: the index's own model must reproduce it, and
   the other model must not. **Both** indexes are checked — #23's delta
   depends on both sides, so verifying only the new one leaves half the
   comparison unexamined.

The second check also fails when the two models are indistinguishable: if the
baseline model reproduces the fine-tuned index's vectors too, the fine-tune did
not move the weights, and a delta between the two indexes would measure
nothing while looking like a legitimate null result.

Usage:
    python scripts/verify_index_parity.py --profile finetuned
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logger = logging.getLogger("verify-index-parity")

DEFAULT_REPORT = "results/index/report.json"

# A float32 vector round-tripped through JSON does not score exactly 1.0
# against itself, but it scores far closer than any two models do.
MATCH_MIN = 0.999
# Measured on the real pair: cos(base, fine-tuned) on sample passages is
# 0.75-0.88. Above this, the two models cannot be told apart.
DISTINCT_MAX = 0.99

# How many mismatched ids to name before summarising the rest.
_EXAMPLES = 5


@dataclass(frozen=True)
class Provenance:
    """How one index's stored vector scores against each of the two models."""

    index: str
    chunk_id: str
    own: float
    other: float


@contextmanager
def profile_unset():
    """Run with ``DUEDILIGENCE_CONFIG_PROFILE`` cleared.

    ``load_config()`` with no argument honours that variable, and the
    documented workflow for this ticket exports it
    (``DUEDILIGENCE_CONFIG_PROFILE=finetuned python scripts/build_index.py``).
    A baseline loaded under it is the candidate, and the whole comparison
    silently becomes an index against itself.
    """
    from duediligence.config import PROFILE_ENV_VAR

    previous = os.environ.pop(PROFILE_ENV_VAR, None)
    try:
        yield
    finally:
        if previous is not None:
            os.environ[PROFILE_ENV_VAR] = previous


def index_counts(client: Any, index: str) -> dict[str, int]:
    """Documents per chunk type, from the aggregation rather than the hit total."""
    response = client.search(
        index=index,
        body={"size": 0, "aggs": {"chunk_type": {"terms": {"field": "chunk_type", "size": 50}}}},
    )
    buckets = response["aggregations"]["chunk_type"]["buckets"]
    return {bucket["key"]: bucket["doc_count"] for bucket in buckets}


def count_problems(baseline: dict[str, int], candidate: dict[str, int]) -> list[str]:
    """Every chunk type whose coverage differs, named with both numbers."""
    problems = []
    for chunk_type in sorted(set(baseline) | set(candidate)):
        expected = baseline.get(chunk_type, 0)
        actual = candidate.get(chunk_type, 0)
        if expected != actual:
            problems.append(f"{chunk_type}: baseline has {expected}, candidate has {actual}")
    return problems


def _summarise(ids: set[str]) -> str:
    shown = sorted(ids)[:_EXAMPLES]
    suffix = f" and {len(ids) - len(shown)} more" if len(ids) > len(shown) else ""
    return ", ".join(shown) + suffix


def coverage_problems(baseline_ids: set[str], candidate_ids: set[str]) -> list[str]:
    """The exact corpus check: which chunks each index has and the other lacks."""
    problems = []
    if missing := baseline_ids - candidate_ids:
        problems.append(
            f"{len(missing)} chunks are in the baseline but not the candidate "
            f"(the candidate build did not finish): {_summarise(missing)}"
        )
    if extra := candidate_ids - baseline_ids:
        problems.append(
            f"{len(extra)} chunks are in the candidate but not the baseline "
            f"(the two indexes were built from different corpora): {_summarise(extra)}"
        )
    return problems


def provenance_problems(
    rows: list[Provenance], *, match_min: float = MATCH_MIN, distinct_max: float = DISTINCT_MAX
) -> list[str]:
    """Whether each sampled vector was written by the model its index names."""
    if not rows:
        return ["no chunks sampled, so nothing was verified"]

    problems = []
    for row in rows:
        if row.own < match_min:
            problems.append(
                f"{row.index}/{row.chunk_id}: the stored vector scores {row.own:.6f} against "
                f"that index's own model (needs >= {match_min}) — this index was built with "
                "a different model"
            )
        if row.other > distinct_max:
            problems.append(
                f"{row.index}/{row.chunk_id}: the *other* model reproduces this stored vector "
                f"at {row.other:.6f} (needs <= {distinct_max}) — the two models are "
                "indistinguishable, so any delta between their indexes measures nothing"
            )
    return problems


def sample_ids(client: Any, index: str, per_type: int) -> list[str]:
    """A spread of chunk ids across types, so parity is not judged on paragraphs alone."""
    response = client.search(
        index=index,
        body={
            "size": 0,
            "aggs": {
                "by_type": {
                    "terms": {"field": "chunk_type", "size": 50},
                    "aggs": {"examples": {"top_hits": {"size": per_type, "_source": False}}},
                }
            },
        },
    )
    return [
        hit["_id"]
        for bucket in response["aggregations"]["by_type"]["buckets"]
        for hit in bucket["examples"]["hits"]["hits"]
    ]


def stored_document(client: Any, index: str, chunk_id: str) -> dict[str, Any] | None:
    """A chunk's stored source, or ``None`` when that index never got it.

    A partial candidate index is the failure this script exists to find, so a
    missing chunk has to become a reported problem. Letting the client's
    ``NotFoundError`` escape would abort before the report is written — losing
    the one output the run promises, in exactly its main failure mode.
    """
    from opensearchpy.exceptions import NotFoundError

    try:
        return client.get(index=index, id=chunk_id)["_source"]
    except NotFoundError:
        return None


def main() -> None:
    import numpy as np
    from opensearchpy.exceptions import NotFoundError

    from duediligence.config import load_config
    from duediligence.index.embed import ChunkEmbedder
    from duediligence.index.opensearch_client import build_client, existing_chunk_ids

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, help="the profile whose index to check")
    parser.add_argument("--per-type", type=int, default=2, help="chunks sampled per chunk type")
    parser.add_argument("--report", default=DEFAULT_REPORT)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # One line per HTTP call otherwise — hundreds of model-resolution requests
    # and one per sampled chunk, which buries the result.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("opensearch").setLevel(logging.WARNING)

    with profile_unset():
        baseline_config = load_config()
    candidate_config = load_config(profile=args.profile)
    client = build_client(baseline_config.opensearch)

    baseline_index = baseline_config.opensearch.index_name
    candidate_index = candidate_config.opensearch.index_name
    if candidate_index == baseline_index:
        raise SystemExit(
            f"profile {args.profile!r} names the same index as the baseline "
            f"({baseline_index}), so there is nothing to compare"
        )

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    def write(report: dict[str, Any]) -> None:
        report_path.write_text(json.dumps(report, indent=2) + "\n")

    try:
        baseline_counts = index_counts(client, baseline_index)
        candidate_counts = index_counts(client, candidate_index)
    except NotFoundError as missing:
        write({"passed": False, "problems": [f"index not found: {missing}"]})
        raise SystemExit(f"index not found — build it first: {missing}") from missing

    baseline_ids = existing_chunk_ids(client, baseline_index)
    candidate_ids = existing_chunk_ids(client, candidate_index)
    coverage = coverage_problems(baseline_ids, candidate_ids) + count_problems(
        baseline_counts, candidate_counts
    )

    models = {
        baseline_index: ChunkEmbedder(baseline_config.models.embedding_model, batch_size=8),
        candidate_index: ChunkEmbedder(candidate_config.models.embedding_model, batch_size=8),
    }

    rows: list[Provenance] = []
    absent: list[str] = []
    for chunk_id in sample_ids(client, baseline_index, args.per_type):
        for index in (baseline_index, candidate_index):
            # The text is read from the index being checked, not carried across
            # from the other one: chunk_id is content-addressed over the
            # pre-enrichment text and enrichment never recomputes it, so the
            # same id can legitimately carry different rolled-up text. Scoring
            # one index's vector against the other's text would report a wrong
            # model where the truth is a different rollup.
            source = stored_document(client, index, chunk_id)
            if source is None:
                absent.append(f"{index}/{chunk_id}: sampled chunk is not in this index")
                continue
            other_index = candidate_index if index == baseline_index else baseline_index
            stored = np.array(source["embedding"], dtype=np.float32)
            own = models[index].embed_passages([source["text"]])[0]
            other = models[other_index].embed_passages([source["text"]])[0]
            rows.append(
                Provenance(
                    index=index,
                    chunk_id=chunk_id,
                    own=float(np.dot(own, stored)),
                    other=float(np.dot(other, stored)),
                )
            )

    problems = coverage + absent + provenance_problems(rows)

    report = {
        "baseline": {"index": baseline_index, "model": baseline_config.models.embedding_model,
                     "counts": baseline_counts, "total": sum(baseline_counts.values())},
        "candidate": {"profile": args.profile, "index": candidate_index,
                      "model": candidate_config.models.embedding_model,
                      "counts": candidate_counts, "total": sum(candidate_counts.values())},
        "coverage_matches": not coverage,
        "coverage_checked_by": "exact chunk_id set diff",
        "sampled_chunks": len(rows),
        "provenance": [
            {"index": r.index, "chunk_id": r.chunk_id,
             "cos_own_model": round(r.own, 6), "cos_other_model": round(r.other, 6)}
            for r in rows
        ],
        "problems": problems,
        "passed": not problems,
    }
    write(report)

    print(f"{baseline_index}: {sum(baseline_counts.values())} docs {baseline_counts}")
    print(f"{candidate_index}: {sum(candidate_counts.values())} docs {candidate_counts}")
    print(f"chunk_id sets identical: {not coverage_problems(baseline_ids, candidate_ids)}")
    print(f"sampled {len(rows)} stored vectors across {len(baseline_counts)} chunk types")
    if rows:
        print(f"  cos against the index's own model: min {min(r.own for r in rows):.6f}")
        print(f"  cos against the other model:       max {max(r.other for r in rows):.6f}")
    for problem in problems:
        print(f"  PROBLEM: {problem}", file=sys.stderr)
    print(f"wrote {report_path}")
    raise SystemExit(1 if problems else 0)


if __name__ == "__main__":
    main()
