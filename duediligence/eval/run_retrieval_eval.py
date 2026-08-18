"""
Retrieval eval: how well does each retriever find the chunk that actually
answers the question?

Scores four retrievers over the same index and the same eval set, in
increasing order of cost:

* **dense** — bge-small-en-v1.5 k-NN. Cheap, semantic.
* **bm25** — OpenSearch BM25 over the english-analyzed text. Cheap, lexical.
* **hybrid** — RRF fusion of the two (``index/hybrid_search.py``).
* **hybrid+rerank** — hybrid candidates reordered by a cross-encoder
  (``index/rerank.py``). Most accurate, most expensive.

Running all four against one fixed eval set is the point: the headline
finding of Phase 5 is the **delta** from the Phase 4 baseline, and a delta
is only meaningful if the eval set, the index, and the metric definitions
are held constant across the comparison.

**The absolute numbers are a lower bound**, for a reason recorded in
``scripts/draft_eval_set.py``: relevance labels come from a sampled
candidate pool rather than exhaustive judgments over all 38k chunks, so a
retriever is scored wrong for returning an unlabeled chunk that does answer
the question. This was confirmed by inspection — for "What is the date of
the merger agreement between Columbia and Umpqua?", the dense retriever's
top three hits all correctly state October 11, 2021 and all counted as
misses. Comparisons *between* retrievers on this fixed set remain sound.

Usage:
    python -m duediligence.eval.run_retrieval_eval
    python -m duediligence.eval.run_retrieval_eval --no-rerank   # skip the slow one
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from collections import defaultdict
from pathlib import Path

from duediligence.config import load_config
from duediligence.eval.eval_set import (
    DEFAULT_EVAL_SET_PATH,
    SPLITS,
    human_verified_count,
    load_eval_set,
    split_counts,
)
from duediligence.eval.retrieval_metrics import aggregate_metrics
from duediligence.index.embed import ChunkEmbedder
from duediligence.index.hybrid_search import hybrid_search
from duediligence.index.opensearch_client import bm25_search, build_client, knn_search
from duediligence.track import flatten_metrics, log_run

logger = logging.getLogger(__name__)

__all__ = ["run_retrieval_eval", "verification_note"]

_K_VALUES = (1, 3, 5, 10, 20)
_CANDIDATE_K = 50

_RETRIEVER_DESCRIPTIONS = {
    "dense": "bge-small-en-v1.5 k-NN (cosine) over chunk embeddings",
    "bm25": "OpenSearch BM25 over the english-analyzed text field",
    "hybrid": f"Reciprocal Rank Fusion of BM25 + dense over {_CANDIDATE_K} candidates each",
    "hybrid_rerank": "hybrid candidates reordered by cross-encoder ms-marco-MiniLM-L-6-v2",
}


def verification_note(*, verified: int, total: int) -> str | None:
    """The disclosure printed under every retrieval report, or ``None``.

    Relevance labels were drafted mechanically, by sampling chunks and
    writing a question for each. Until a human has read a question and
    confirmed its label, every number scored against it is self-graded.
    That is a legitimate thing to publish and an illegitimate thing to
    publish silently, so the count travels with the metrics and an
    incomplete count says out loud that it is incomplete.
    """
    if total and verified >= total:
        return None
    if verified == 0:
        return (
            "NOTE: no eval entries are human-verified — every question was "
            "drafted automatically from a sampled chunk. Numbers are "
            "provisional until a sample is checked."
        )
    return (
        f"NOTE: {verified} of {total} eval entries are human-verified; the "
        "rest were drafted automatically from sampled chunks. Numbers over "
        "the unverified remainder are provisional."
    )


def run_retrieval_eval(
    eval_set_path: str = DEFAULT_EVAL_SET_PATH,
    *,
    k: int = 20,
    rerank: bool = True,
    config_path: str = "config/config.yaml",
    split: str | None = None,
) -> dict:
    # ``split=None`` scores every question, which is what reproduces the
    # published comparison table. The headline fine-tune delta is reported on
    # ``split="test"``, which no tuning sweep is allowed to touch.
    entries = load_eval_set(eval_set_path, split=split)
    config = load_config(config_path)
    client = build_client(config.opensearch)
    index_name = config.opensearch.index_name
    embedder = ChunkEmbedder(config.models.embedding_model)

    reranker = None
    if rerank:
        from duediligence.index.rerank import CrossEncoderReranker

        reranker = CrossEncoderReranker(config.models.reranker_model)

    # One batched encode for every question rather than one call per query.
    questions = [entry["question"] for entry in entries]
    query_vectors = embedder.embed_queries(questions)

    per_query: list[dict] = []
    latencies: dict[str, list[float]] = defaultdict(list)

    for entry, vector in zip(entries, query_vectors, strict=True):
        listed = vector.tolist()
        retrieved: dict[str, list[str]] = {}

        started = time.perf_counter()
        retrieved["dense"] = [h["chunk_id"] for h in knn_search(client, index_name, listed, k=k)]
        latencies["dense"].append((time.perf_counter() - started) * 1000)

        started = time.perf_counter()
        retrieved["bm25"] = [
            h["chunk_id"] for h in bm25_search(client, index_name, entry["question"], k=k)
        ]
        latencies["bm25"].append((time.perf_counter() - started) * 1000)

        started = time.perf_counter()
        hybrid_hits = hybrid_search(
            client, index_name, entry["question"], listed, k=k, candidate_k=_CANDIDATE_K
        )
        latencies["hybrid"].append((time.perf_counter() - started) * 1000)
        retrieved["hybrid"] = [h["chunk_id"] for h in hybrid_hits]

        if reranker is not None:
            # Rerank the same fused candidate pool the hybrid row scored, so
            # the two rows differ only by the reranking step.
            started = time.perf_counter()
            candidates = hybrid_search(
                client, index_name, entry["question"], listed,
                k=_CANDIDATE_K, candidate_k=_CANDIDATE_K,
            )
            reranked = reranker.rerank(entry["question"], candidates, top_k=k)
            latencies["hybrid_rerank"].append((time.perf_counter() - started) * 1000)
            retrieved["hybrid_rerank"] = [h["chunk_id"] for h in reranked]

        relevant = set(entry["relevant_chunk_ids"])
        row = {
            "eval_id": entry["eval_id"],
            "question": entry["question"],
            "question_type": entry["question_type"],
            "company": entry["company"],
            "chunk_type": entry["chunk_type"],
            "relevant_chunk_ids": entry["relevant_chunk_ids"],
            "verified": entry.get("verified", False),
        }
        for name, ids in retrieved.items():
            row[f"{name}_retrieved"] = ids
            row[f"{name}_rank"] = next((i + 1 for i, c in enumerate(ids) if c in relevant), None)
        per_query.append(row)

    retriever_names = ["dense", "bm25", "hybrid"] + (["hybrid_rerank"] if reranker else [])

    def _metrics(name: str) -> dict[str, float]:
        return aggregate_metrics(
            [(row[f"{name}_retrieved"], set(row["relevant_chunk_ids"])) for row in per_query],
            k_values=_K_VALUES,
        )

    def _by_group(name: str, group_key: str) -> dict[str, dict[str, float]]:
        grouped: dict[str, list] = defaultdict(list)
        for row in per_query:
            grouped[row[group_key]].append(
                (row[f"{name}_retrieved"], set(row["relevant_chunk_ids"]))
            )
        return {
            group: aggregate_metrics(pairs, k_values=(1, 5, 10))
            for group, pairs in sorted(grouped.items())
        }

    baseline = _metrics("bm25")
    report = {
        "eval_set": eval_set_path,
        "split": split or "all",
        "split_sizes": split_counts(load_eval_set(eval_set_path)),
        "queries": len(per_query),
        "human_verified_queries": human_verified_count(per_query),
        "index": index_name,
        "embedding_model": config.models.embedding_model,
        "reranker_model": config.models.reranker_model if reranker else None,
        "k": k,
        "candidate_k": _CANDIDATE_K,
        "ground_truth_caveat": (
            "Relevance labels come from a stratified sampled candidate pool, not "
            "exhaustive judgments over the full corpus; unlabeled chunks that also "
            "answer a question score as misses, so these are lower bounds. Questions "
            "were also drafted by reading the labeled chunks, which shares vocabulary "
            "with them and structurally favors lexical matching."
        ),
        "retrievers": {
            name: {
                "description": _RETRIEVER_DESCRIPTIONS[name],
                "metrics": _metrics(name),
                "latency_ms_mean": sum(latencies[name]) / len(latencies[name]),
                "by_question_type": _by_group(name, "question_type"),
                "by_chunk_type": _by_group(name, "chunk_type"),
            }
            for name in retriever_names
        },
        "per_query": per_query,
    }

    # The delta against the strongest single retriever is the Phase 5
    # finding, so it is computed here rather than left for a reader to do
    # arithmetic on two tables.
    report["improvement_over_best_single_retriever"] = {
        name: {
            metric: round(report["retrievers"][name]["metrics"][metric] - baseline[metric], 4)
            for metric in ("recall@1", "recall@5", "recall@10", "mrr", "ndcg@10")
        }
        for name in retriever_names
    }
    return report


def _print_table(report: dict) -> None:
    columns = ("recall@1", "recall@5", "recall@10", "hit_rate@10", "mrr", "ndcg@10")
    header = f"{'retriever':<15}" + "".join(f"{c:>13}" for c in columns) + f"{'ms/query':>11}"
    print(header)
    print("-" * len(header))
    for name, payload in report["retrievers"].items():
        m = payload["metrics"]
        print(
            f"{name:<15}"
            + "".join(f"{m[c]:>13.3f}" for c in columns)
            + f"{payload['latency_ms_mean']:>11.1f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", default=DEFAULT_EVAL_SET_PATH)
    parser.add_argument(
        "--split",
        choices=SPLITS,
        default=None,
        help="score one split only; omit to score every question (the published table)",
    )
    parser.add_argument("--k", type=int, default=20)
    parser.add_argument("--no-rerank", action="store_true", help="skip cross-encoder reranking")
    parser.add_argument("--out", default="results/retrieval/report.json")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)
    report = run_retrieval_eval(
        args.eval_set, k=args.k, rerank=not args.no_rerank, split=args.split
    )

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")

    # The report file stays the source of truth; this is additive, and a
    # no-op without WANDB_API_KEY.
    run_url = log_run(
        name="retrieval-eval",
        tags=["retrieval", "eval"],
        config={
            "eval_set": report["eval_set"],
            "index": report["index"],
            "embedding_model": report["embedding_model"],
            "reranker_model": report["reranker_model"],
            "k": report["k"],
            "candidate_k": report["candidate_k"],
            "queries": report["queries"],
            # Which questions produced these numbers. A tracked run that does
            # not say so is indistinguishable from one scored on everything.
            "split": report["split"],
            # Logged as configuration rather than as a metric: how much of
            # the eval set a human has checked is a property of the run, and
            # every reported number should be read against it.
            "human_verified_queries": report["human_verified_queries"],
        },
        metrics=flatten_metrics(report),
    )

    print(f"retrieval eval over {report['queries']} queries "
          f"from the {report['split']} split "
          f"({report['human_verified_queries']} human-verified)\n")
    if run_url:
        print(f"tracked: {run_url}\n")
    _print_table(report)

    print("\nby question type (recall@10):")
    for name, payload in report["retrievers"].items():
        rendered = "  ".join(
            f"{group}={values['recall@10']:.2f}"
            for group, values in payload["by_question_type"].items()
        )
        print(f"  {name:<14} {rendered}")

    print("\ndelta vs BM25 (the best single retriever at baseline):")
    for name, deltas in report["improvement_over_best_single_retriever"].items():
        rendered = "  ".join(f"{metric}={value:+.3f}" for metric, value in deltas.items())
        print(f"  {name:<14} {rendered}")

    note = verification_note(
        verified=report["human_verified_queries"], total=report["queries"]
    )
    if note:
        print(f"\n{note}")
    print(f"\nwrote {output_path}")


if __name__ == "__main__":
    main()
