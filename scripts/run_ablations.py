"""
Phase 5 ablations — three questions the headline table raised but can't answer.

**A. RRF fusion weight.** Equal-weight fusion of BM25 and dense *lowered*
precision against BM25 alone (recall@1 -0.099, MRR -0.087) while raising
deep recall slightly. The obvious suspicion is that the dense retriever is
simply much weaker here (recall@10 0.322 vs 0.604) and equal weighting lets
it push weak candidates into the top ranks. Sweeping the dense weight from
0 (pure BM25) to 1 (equal) tests that directly.

**B. Chunking / hierarchy level.** Does having document- and section-level
chunks in the searchable pool help retrieval, or do they act as
distractors? Held fair by fixing the query set to those whose ground truth
is a paragraph or table chunk, and varying only which chunk types are
*searchable*. A level that is never the right answer can only help by
providing context or hurt by crowding — this measures which.

**C. Reranking candidate depth.** The cross-encoder is 27x slower than
BM25, and cost scales with the candidate pool. If depth 25 captures most of
the gain of depth 100, that is the configuration the API should ship.

Writes results/ablations/report.json.

Usage:
    python scripts/run_ablations.py
    python scripts/run_ablations.py --skip-rerank    # A and B only (fast)
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.config import load_config
from duediligence.eval.retrieval_metrics import aggregate_metrics
from duediligence.index.embed import ChunkEmbedder
from duediligence.index.hybrid_search import hybrid_search
from duediligence.index.opensearch_client import bm25_search, build_client, knn_search

logger = logging.getLogger("ablations")

_METRICS = ("recall@1", "recall@5", "recall@10", "mrr", "ndcg@10")
_K = 20


def _load_eval_set(path: str = "data/eval_set.jsonl") -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def _score(pairs: list[tuple[list[str], set[str]]]) -> dict[str, float]:
    metrics = aggregate_metrics(pairs, k_values=(1, 5, 10, 20))
    return {m: round(metrics[m], 4) for m in _METRICS}


def ablate_fusion_weight(client, index, embedder, entries, vectors) -> list[dict]:
    """A: sweep the dense retriever's weight in the RRF fusion."""
    results = []
    for dense_weight in (0.0, 0.25, 0.5, 0.75, 1.0):
        pairs = []
        for entry, vector in zip(entries, vectors, strict=True):
            hits = hybrid_search(
                client, index, entry["question"], vector.tolist(),
                k=_K, candidate_k=50, weights=[1.0, dense_weight],
            )
            pairs.append(([h["chunk_id"] for h in hits], set(entry["relevant_chunk_ids"])))
        results.append({"dense_weight": dense_weight, "metrics": _score(pairs)})
        logger.info("fusion weight %.2f -> %s", dense_weight, results[-1]["metrics"])
    return results


def ablate_chunk_levels(client, index, embedder, entries, vectors) -> list[dict]:
    """B: vary which hierarchy levels are searchable, on a fixed query set.

    Scored **only on queries whose ground truth is a paragraph chunk**, so
    that every configuration below can actually reach the right answer. This
    matters: an earlier version of this ablation also scored table-ground-
    truth queries, which made the paragraph-only configuration look
    catastrophically worse (recall@10 0.35 vs 0.57) when in fact it had
    simply been asked to find documents it was forbidden from returning.
    That is a measurement artifact, not a chunking finding.

    With the query set fixed this way, the comparison asks the real
    question: do the *other* hierarchy levels help as context or hurt as
    distractors, when the answer is always a paragraph?
    """
    scoreable = [
        (entry, vector)
        for entry, vector in zip(entries, vectors, strict=True)
        if entry["chunk_type"] == "paragraph"
    ]

    configurations = {
        "all_levels": None,  # no filter: document + section + paragraph + table + chart
        "paragraph_table_only": ["paragraph", "table"],
        "paragraph_only": ["paragraph"],
    }

    results = []
    for name, allowed in configurations.items():
        pairs = []
        for entry, vector in scoreable:
            # A terms filter restricts the searchable pool without
            # reindexing, which keeps every configuration on identical
            # embeddings and identical BM25 statistics.
            filters = {"chunk_type": allowed} if allowed else None
            hits = hybrid_search(
                client, index, entry["question"], vector.tolist(),
                k=_K, candidate_k=50, filters=filters,
            )
            pairs.append(([h["chunk_id"] for h in hits], set(entry["relevant_chunk_ids"])))
        results.append({
            "searchable_levels": name,
            "queries": len(scoreable),
            "scored_on": "queries whose ground-truth chunk is a paragraph (reachable in every config)",
            "metrics": _score(pairs),
        })
        logger.info("levels %s -> %s", name, results[-1]["metrics"])
    return results


def ablate_rerank_depth(client, index, embedder, entries, vectors, reranker) -> list[dict]:
    """C: how deep the reranker's candidate pool needs to be."""
    results = []
    for candidate_k in (10, 25, 50, 100):
        pairs = []
        started = time.perf_counter()
        for entry, vector in zip(entries, vectors, strict=True):
            candidates = hybrid_search(
                client, index, entry["question"], vector.tolist(),
                k=candidate_k, candidate_k=candidate_k,
            )
            reranked = reranker.rerank(entry["question"], candidates, top_k=_K)
            pairs.append(([h["chunk_id"] for h in reranked], set(entry["relevant_chunk_ids"])))
        elapsed_ms = (time.perf_counter() - started) * 1000 / len(entries)
        results.append(
            {"candidate_k": candidate_k, "metrics": _score(pairs), "latency_ms_mean": round(elapsed_ms, 1)}
        )
        logger.info("rerank depth %d -> %s (%.0f ms)", candidate_k, results[-1]["metrics"], elapsed_ms)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-rerank", action="store_true", help="skip ablation C (the slow one)")
    parser.add_argument("--out", default="results/ablations/report.json")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    logging.getLogger("opensearch").setLevel(logging.WARNING)

    config = load_config()
    client = build_client(config.opensearch)
    index = config.opensearch.index_name
    embedder = ChunkEmbedder(config.models.embedding_model)

    entries = _load_eval_set()
    vectors = embedder.embed_queries([e["question"] for e in entries])

    # Single-retriever reference rows, so the ablation report stands alone.
    baselines = {}
    for name, fn in (
        ("bm25", lambda e, v: bm25_search(client, index, e["question"], k=_K)),
        ("dense", lambda e, v: knn_search(client, index, v.tolist(), k=_K)),
    ):
        pairs = [
            ([h["chunk_id"] for h in fn(entry, vector)], set(entry["relevant_chunk_ids"]))
            for entry, vector in zip(entries, vectors, strict=True)
        ]
        baselines[name] = _score(pairs)

    report = {
        "eval_set": "data/eval_set.jsonl",
        "queries": len(entries),
        "human_verified_queries": sum(1 for e in entries if e.get("verified")),
        "baselines": baselines,
        "ablation_a_fusion_weight": ablate_fusion_weight(client, index, embedder, entries, vectors),
        "ablation_b_chunk_levels": ablate_chunk_levels(client, index, embedder, entries, vectors),
    }

    if not args.skip_rerank:
        from duediligence.index.rerank import CrossEncoderReranker

        reranker = CrossEncoderReranker(config.models.reranker_model)
        report["ablation_c_rerank_depth"] = ablate_rerank_depth(
            client, index, embedder, entries, vectors, reranker
        )

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")

    print("\n=== A. RRF dense weight (1.0 = equal weighting) ===")
    print(f"{'dense_w':>8}" + "".join(f"{m:>12}" for m in _METRICS))
    for row in report["ablation_a_fusion_weight"]:
        print(f"{row['dense_weight']:>8.2f}" + "".join(f"{row['metrics'][m]:>12.3f}" for m in _METRICS))

    b_queries = report["ablation_b_chunk_levels"][0]["queries"]
    print(f"\n=== B. Searchable hierarchy levels ({b_queries} paragraph-ground-truth queries) ===")
    print(f"{'levels':>22}" + "".join(f"{m:>12}" for m in _METRICS))
    for row in report["ablation_b_chunk_levels"]:
        print(f"{row['searchable_levels']:>22}" + "".join(f"{row['metrics'][m]:>12.3f}" for m in _METRICS))

    if "ablation_c_rerank_depth" in report:
        print("\n=== C. Reranker candidate depth ===")
        print(f"{'cand_k':>8}" + "".join(f"{m:>12}" for m in _METRICS) + f"{'ms/query':>11}")
        for row in report["ablation_c_rerank_depth"]:
            print(
                f"{row['candidate_k']:>8}"
                + "".join(f"{row['metrics'][m]:>12.3f}" for m in _METRICS)
                + f"{row['latency_ms_mean']:>11.1f}"
            )

    print(f"\nwrote {output}")


if __name__ == "__main__":
    main()
