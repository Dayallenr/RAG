"""
Why the reranked cell of the fine-tune matrix shows a delta of exactly zero.

The four-run matrix reported the fine-tuned bi-encoder lifting dense
recall@10 substantially while the reranked row did not move by a thousandth
on any metric, and the reranked result lists came back byte-identical across
two arms that provably queried different indexes. That is not the reranker
absorbing an improvement — it is the reranker never seeing it.

This script measures the mechanism. The cross-encoder reranks the *fused
candidate pool*, and RRF scores a document ``weight / (rrf_k + rank)``. With
the shipped dense weight of 0.25 and ``rrf_k`` 60, the best a dense-only
document can score is ``0.25 / 61``, while BM25's last in-pool document at
depth ``c`` scores ``1 / (60 + c)``. The first exceeds the second only once
``c > 184``, so at the configured depth of 50 **no document dense retrieval
found alone can enter the pool at all** — the fine-tuned vectors reorder the
pool and never change its membership, and reordering is precisely what a
cross-encoder throws away.

That is arithmetic, so this script checks it against the live index rather
than trusting it: it rebuilds each arm's fused pool and compares it to that
arm's BM25 candidates and to the other arm's pool.

Writes results/finetune_delta/rerank_pool.json.

Usage:
    python scripts/verify_rerank_pool.py
    python scripts/verify_rerank_pool.py --split all
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.config import PROFILE_ENV_VAR, load_config
from duediligence.eval.eval_set import SPLITS, load_eval_set
from duediligence.index.embed import ChunkEmbedder
from duediligence.index.hybrid_search import DEFAULT_RRF_K, hybrid_search
from duediligence.index.opensearch_client import bm25_search, build_client

logger = logging.getLogger("rerank-pool")

DEFAULT_OUT = Path("results/finetune_delta/rerank_pool.json")
_ARMS = (("base", None), ("finetuned", "finetuned"))


def dense_only_depth_threshold(dense_weight: float, rrf_k: int = DEFAULT_RRF_K) -> int:
    """The BM25 candidate depth at which a dense-only document can first
    enter the fused pool.

    A dense-only document's best possible score is ``dense_weight / (k + 1)``.
    BM25's document at depth ``c`` scores ``1 / (k + c)``. Solving for the
    depth at which the former wins gives the answer below — under it, the
    fused pool's membership is BM25's alone, whatever the embedding model.
    """
    if dense_weight <= 0:
        return 0
    return int((rrf_k + 1) / dense_weight) - rrf_k


def arm_config(profile: str | None):
    """Load one arm's config, ignoring whatever profile the shell has exported.

    ``load_config`` falls back to ``DUEDILIGENCE_CONFIG_PROFILE`` when no
    profile is passed, and that variable is exported in exactly the situation
    this script runs in — while working on the fine-tuned index. An arm that
    picked it up would compare the fine-tuned index against itself and report
    pools identical on 30/30, which is the number this script exists to
    produce. Both arms are named explicitly here, so the ambient value is
    removed for the load and put back afterwards.
    """
    saved = os.environ.pop(PROFILE_ENV_VAR, None)
    try:
        return load_config(profile=profile)
    finally:
        if saved is not None:
            os.environ[PROFILE_ENV_VAR] = saved


def collect_pools(
    entries: list[dict], profile: str | None, candidate_k: int, dense_weight: float
) -> dict:
    config = arm_config(profile)
    client = build_client(config.opensearch)
    index = config.opensearch.index_name
    embedder = ChunkEmbedder(config.models.embedding_model)
    vectors = embedder.embed_queries([entry["question"] for entry in entries])

    pools, bm25 = [], []
    for entry, vector in zip(entries, vectors, strict=True):
        pools.append([
            hit["chunk_id"] for hit in hybrid_search(
                client, index, entry["question"], vector.tolist(),
                k=candidate_k, candidate_k=candidate_k,
                # The weight the threshold below is computed from has to be
                # the weight the pools were actually built with, or the report
                # contradicts itself with no error.
                weights=[1.0, dense_weight],
            )
        ])
        bm25.append([
            hit["chunk_id"]
            for hit in bm25_search(client, index, entry["question"], k=candidate_k)
        ])
    return {
        "index": index,
        "embedding_model": config.models.embedding_model,
        "pools": pools,
        "bm25": bm25,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=[*SPLITS, "all"], default="test")
    parser.add_argument("--candidate-k", type=int, default=50)
    parser.add_argument("--dense-weight", type=float, default=0.25)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    entries = load_eval_set(split=None if args.split == "all" else args.split)
    arms = {}
    for name, profile in _ARMS:
        logger.info("collecting %s candidate pools", name)
        arms[name] = collect_pools(entries, profile, args.candidate_k, args.dense_weight)

    base, finetuned = arms["base"], arms["finetuned"]
    if base["index"] == finetuned["index"]:
        raise SystemExit(
            f"both arms resolved to {base['index']!r}. Every count below would "
            "be an index compared with itself, which reads as a perfect match. "
            "Check config/profiles/finetuned.yaml."
        )
    pool_is_bm25 = sum(
        set(pool) == set(bm25) for pool, bm25 in zip(base["pools"], base["bm25"], strict=True)
    )
    pool_is_bm25_finetuned = sum(
        set(pool) == set(bm25)
        for pool, bm25 in zip(finetuned["pools"], finetuned["bm25"], strict=True)
    )
    same_membership = sum(
        set(a) == set(b) for a, b in zip(base["pools"], finetuned["pools"], strict=True)
    )
    same_order = sum(
        a == b for a, b in zip(base["pools"], finetuned["pools"], strict=True)
    )
    jaccard = mean(
        len(set(a) & set(b)) / len(set(a) | set(b))
        for a, b in zip(base["pools"], finetuned["pools"], strict=True)
    )

    threshold = dense_only_depth_threshold(args.dense_weight)
    report = {
        "question": (
            "does the fine-tuned bi-encoder change which documents the "
            "cross-encoder reranks, or only their order?"
        ),
        "eval_split": args.split,
        "queries": len(entries),
        "candidate_k": args.candidate_k,
        "dense_weight": args.dense_weight,
        "rrf_k": DEFAULT_RRF_K,
        "arms": {
            name: {"index": arm["index"], "embedding_model": arm["embedding_model"]}
            for name, arm in arms.items()
        },
        "pool_equals_bm25_candidates": pool_is_bm25,
        "pool_equals_bm25_candidates_finetuned": pool_is_bm25_finetuned,
        "pools_identical_as_sets_across_arms": same_membership,
        "pools_identical_in_order_across_arms": same_order,
        "mean_pool_jaccard_across_arms": round(jaccard, 4),
        "dense_only_entry_depth": threshold,
        "finding": (
            f"At dense weight {args.dense_weight} and rrf_k {DEFAULT_RRF_K}, a "
            f"document found by dense retrieval alone cannot enter the fused "
            f"pool until the candidate depth exceeds {threshold}; the pipeline "
            f"runs at {args.candidate_k}. The pool's membership is therefore "
            "BM25's, and the bi-encoder only reorders it — which is the one "
            "thing a cross-encoder discards. A null reranked delta under this "
            "configuration is a property of the fusion settings, not evidence "
            "about the fine-tuned model."
        ),
    }

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")

    print(f"\n{args.split} split, {len(entries)} questions, candidate_k={args.candidate_k}")
    print(f"  fused pool == BM25 candidates (base)      : {pool_is_bm25}/{len(entries)}")
    print(f"  fused pool == BM25 candidates (fine-tuned): {pool_is_bm25_finetuned}/{len(entries)}")
    print(f"  pools identical as sets across arms       : {same_membership}/{len(entries)}")
    print(f"  pools identical in order across arms      : {same_order}/{len(entries)}")
    print(f"  dense-only documents enter the pool only past depth {threshold}")
    print(f"\nwrote {output}")


if __name__ == "__main__":
    main()
