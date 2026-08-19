"""Sweep the ANN parameters into a recall-versus-latency curve (#14).

Every vector index in this project was built and queried on OpenSearch's
default HNSW settings — ``m=16``, ``ef_construction=128``, and no ``ef_search``
at all. That is a defensible default and an unmeasured one: nothing here said
what the approximate search was giving up against exact nearest neighbours, or
what buying it back would cost. This measures both.

**Two experiments, kept apart on purpose.**

*Search-time*, on the served index itself. ``ef_search`` widens the HNSW
candidate queue per query and needs no rebuild, so this arm is measured
directly against ``duediligence-chunks-finetuned`` with nothing copied,
nothing merged and no confound to state. It is the one that can change a
deployment today, and it is where the operating point is chosen.

*Build-time*, on copies. ``m`` and ``ef_construction`` are baked into the graph
at index time, so each pair needs its own index. Those are made with
``_reindex``, which copies the stored vectors as they are — the fine-tuned
model is never re-run, and this machine (8 GB, and it swaps) never has to
re-embed 38,483 chunks to answer a systems question. The copies carry only
``chunk_id`` and ``embedding``, and are force-merged to one segment so that
the only difference between them is the two parameters being swept.

**The confound in the build sweep, stated rather than buried.** Those copies
differ from the served index in three ways at once: one segment instead of
seven, no ``text`` field to fetch, and the swept parameters. Only the third is
of interest, and the family is internally comparable — ``m16-efc128`` is in the
grid precisely so the served index's own build configuration appears in it —
but a copy's absolute latency is *not* the served index's latency, and this
report never subtracts one from the other.

**Ground truth is brute force, not a better approximation.** ``match_all`` plus
the k-NN plugin's ``knn_score`` script scores every document in the corpus and
consults no graph, so the ranking it returns is exact by construction. ANN
recall here is the standard one — how much of the true top-k the graph
actually reached — and it is reported next to the labelled end-task metrics,
because those answer different questions: a search can lose true neighbours
that no eval label ever pointed at, and a search can reach every true
neighbour of a query whose answer is not in the corpus.

Usage:
    python scripts/sweep_ann.py --profile finetuned
    python scripts/sweep_ann.py --profile finetuned --skip-build-sweep
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.config import load_config  # noqa: E402
from duediligence.eval.eval_set import (  # noqa: E402
    DEFAULT_EVAL_SET_PATH,
    SPLITS,
    human_verified_count,
    load_eval_set,
)
from duediligence.eval.retrieval_metrics import aggregate_metrics  # noqa: E402
from duediligence.index.embed import ChunkEmbedder  # noqa: E402
from duediligence.index.hybrid_search import hybrid_search  # noqa: E402
from duediligence.index.opensearch_client import (  # noqa: E402
    DEFAULT_EF_CONSTRUCTION,
    DEFAULT_M,
    build_client,
    build_index_mapping,
    document_count,
    exact_knn_search,
    knn_search,
)
from duediligence.track import flatten_metrics, log_run  # noqa: E402

logger = logging.getLogger("sweep-ann")

DEFAULT_REPORT = "results/ann_sweep/report.json"
RUN_NAME = "ann-sweep"

#: Every index this script creates is named under this prefix, and every index
#: it deletes has to start with it. The sweep's cleanup is the one thing here
#: that can destroy a corpus, so the namespace is enforced rather than assumed.
SWEEP_PREFIX = "ann-sweep-"

#: Both depths this project actually retrieves at: 10 is what the dense arm of
#: the retrieval eval asks for, 50 is the candidate depth hybrid search feeds
#: the reranker. A curve at a depth nothing runs at would be decoration.
DEFAULT_K_VALUES = (10, 50)

DEFAULT_EF_SEARCH = (50, 100, 200, 400, 800)
DEFAULT_M_VALUES = (8, 16, 32)
DEFAULT_EF_CONSTRUCTION_VALUES = (64, 128, 256)

#: The operating point is the cheapest configuration reaching this much of the
#: exact result. 0.99 rather than 1.0 because the last percent of ANN recall is
#: where the latency curve turns vertical, and because the labelled metrics
#: below it are already saturated well before it.
DEFAULT_TARGET_ANN_RECALL = 0.99

#: Scored at the same depths as every other retrieval report here, so the rows
#: can be read against results/retrieval/report.json without re-deriving them.
_METRIC_K = (1, 5, 10)

_HEADLINE_METRIC = "recall@10"


@dataclass(frozen=True)
class BuildConfig:
    """One HNSW build configuration: a graph degree and a construction width."""

    m: int
    ef_construction: int

    @property
    def label(self) -> str:
        return f"m{self.m}-efc{self.ef_construction}"


def build_grid(m_values: list[int], ef_construction_values: list[int]) -> list[BuildConfig]:
    """The cross product, in a stable order so two runs list configs alike."""
    return [
        BuildConfig(m=m, ef_construction=ef_construction)
        for m in m_values
        for ef_construction in ef_construction_values
    ]


def sweep_index_name(source_index: str, config: BuildConfig) -> str:
    """Where a swept copy of ``source_index`` lives.

    Namespaced under :data:`SWEEP_PREFIX` and carrying the source's name, so
    the cleanup that deletes these can refuse anything outside the namespace
    and two source indexes' sweeps cannot overwrite each other.
    """
    return f"{SWEEP_PREFIX}{source_index}-{config.label}"


def percentile(values: list[float], fraction: float) -> float:
    """Nearest-rank percentile — no interpolation.

    Same definition as the ONNX benchmark's, and for the same reason: an
    interpolated p95 over a hundred-odd samples reports a latency that no
    single query produced.
    """
    if not values:
        raise ValueError("no values to take a percentile of")
    ordered = sorted(values)
    rank = max(1, min(len(ordered), int(round(fraction * len(ordered)))))
    return ordered[rank - 1]


def latency_summary(per_query_ms: list[float]) -> dict[str, float]:
    return {
        "mean": sum(per_query_ms) / len(per_query_ms),
        "p50": percentile(per_query_ms, 0.50),
        "p95": percentile(per_query_ms, 0.95),
        "samples": len(per_query_ms),
    }


def ann_recall(approximate: list[str], exact: list[str], k: int) -> float:
    """Fraction of the true top-k neighbours the approximate search reached.

    Set overlap, not rank agreement: this asks what the graph traversal found,
    and how the engine then ordered what it found is what the labelled nDCG and
    MRR in ``retrieval`` measure.

    Divided by the size of the reference rather than by ``k``, so a query whose
    ground truth is shorter than ``k`` — a corpus smaller than the requested
    depth — is not scored against neighbours that do not exist.
    """
    reference = set(exact[:k])
    if not reference:
        return 0.0
    return len(reference & set(approximate[:k])) / len(reference)


def search_points(values: list[int], k: int) -> list[int | None]:
    """The ef_search values to measure at depth ``k``, default first.

    ``None`` is the engine default (Lucene searches at ``ef = k``) and is the
    configuration every number this project has published was measured at, so
    it anchors the curve. Values below ``k`` are dropped rather than clamped:
    the engine answers them with a short result list instead of an error, and
    silently raising them to ``k`` would put a point on the curve labelled with
    a width that was never searched.
    """
    return [None, *sorted({value for value in values if value >= k})]


def choose_operating_point(
    points: list[dict[str, Any]], *, target: float
) -> tuple[dict[str, Any], bool]:
    """The cheapest point reaching ``target`` ANN recall, and whether one did.

    Ties on recall go to the lower p95 latency, and then to the smaller
    ef_search — the default (``None``) counts as smallest, because leaving a
    parameter alone is cheaper to operate than setting it.

    When nothing reaches the target the best-recall point is returned with
    ``False`` rather than the last point with ``True``: "this met the bar" and
    "nothing met the bar, here is the best there was" have to stay
    distinguishable in the report.
    """
    if not points:
        raise ValueError("no curve points to choose an operating point from")

    def cost(point: dict[str, Any]) -> tuple[float, int]:
        return (point["latency_ms"]["p95"], point["ef_search"] or 0)

    reaching = [point for point in points if point["ann_recall"] >= target]
    if reaching:
        return min(reaching, key=cost), True
    return max(points, key=lambda p: (p["ann_recall"], -p["latency_ms"]["p95"])), False


def _point_label(point: dict[str, Any]) -> str:
    if point["ef_search"] is None:
        return "the engine default (ef_search unset, ef = k)"
    return f"ef_search={point['ef_search']}"


def justification(
    chosen: dict[str, Any], baseline: dict[str, Any], *, reached: bool, target: float
) -> str:
    """State why this point, from the curve, in one sentence.

    Written from the measurements rather than by hand so it cannot outlive the
    run that produced it — a justification that still reads well after a re-run
    changed the numbers is exactly the stale claim this project's prime
    directive exists to prevent.
    """
    k = chosen["k"]
    ratio = chosen["latency_ms"]["p95"] / baseline["latency_ms"]["p95"]
    task = chosen["retrieval"].get(_HEADLINE_METRIC)
    task_delta = task - baseline["retrieval"].get(_HEADLINE_METRIC, task)

    if chosen["ef_search"] == baseline["ef_search"]:
        head = (
            f"At k={k} the default already reaches ANN recall {chosen['ann_recall']:.3f} "
            f"at p95 {chosen['latency_ms']['p95']:.1f} ms, so the operating point is "
            "unchanged"
        )
    else:
        head = (
            f"At k={k}, {_point_label(chosen)} reaches ANN recall "
            f"{chosen['ann_recall']:.3f} against the default's "
            f"{baseline['ann_recall']:.3f}, for p95 {chosen['latency_ms']['p95']:.1f} ms "
            f"against {baseline['latency_ms']['p95']:.1f} ms ({ratio:.2f}x)"
        )

    if reached:
        tail = f", clearing the {target:.2f} ANN-recall target"
    else:
        tail = (
            f", but the curve does not reach the {target:.2f} ANN-recall target — this "
            "is the highest-recall point measured, not a chosen trade-off"
        )

    return (
        f"{head}{tail}. Labelled dense {_HEADLINE_METRIC} is {task:.3f} "
        f"({task_delta:+.3f} against the default)."
    )


def measure_point(
    *,
    client,
    index_name: str,
    build_label: str,
    entries: list[dict],
    vectors: list[list[float]],
    ground_truth: list[list[str]],
    k: int,
    ef_search: int | None,
    repeats: int,
) -> dict[str, Any]:
    """One point on the curve: recall against exact, latency, and end-task score.

    Timed with a warmup pass first and then ``repeats`` full passes over the
    question set. Warmup is not optional on this project's hardware — a traced
    first request once recorded 2,995 ms against a steady state of tens of
    milliseconds, and a curve whose first point paid that warmup would show a
    latency cliff that is an artefact of measurement order.
    """
    for vector in vectors[: min(8, len(vectors))]:
        knn_search(client, index_name, vector, k=k, ef_search=ef_search)

    per_query_ms: list[float] = []
    retrieved: list[list[str]] | None = None
    repeats_identical = True
    for _ in range(repeats):
        lists = []
        for vector in vectors:
            started = time.perf_counter()
            hits = knn_search(client, index_name, vector, k=k, ef_search=ef_search)
            per_query_ms.append((time.perf_counter() - started) * 1000)
            lists.append([hit["chunk_id"] for hit in hits])
        if retrieved is None:
            retrieved = lists
        elif lists != retrieved:
            # HNSW search is deterministic against a fixed graph. If two
            # passes disagree, the latency spread is not the only thing that
            # moved and every recall figure below is a sample rather than a
            # measurement.
            repeats_identical = False

    assert retrieved is not None
    recalls = [
        ann_recall(approximate, exact, k)
        for approximate, exact in zip(retrieved, ground_truth, strict=True)
    ]
    metrics = aggregate_metrics(
        [
            (hits, set(entry["relevant_chunk_ids"]))
            for hits, entry in zip(retrieved, entries, strict=True)
        ],
        k_values=_METRIC_K,
    )
    return {
        "build": build_label,
        "k": k,
        "ef_search": ef_search,
        "ann_recall": sum(recalls) / len(recalls),
        "ann_recall_min": min(recalls),
        "queries_matching_exact_exactly": sum(
            1
            for approximate, exact in zip(retrieved, ground_truth, strict=True)
            if approximate == exact[:k]
        ),
        "latency_ms": latency_summary(per_query_ms),
        "retrieval": metrics,
        "repeat_lists_identical": repeats_identical,
    }


def exact_ground_truth(
    *, client, index_name: str, vectors: list[list[float]], depth: int
) -> tuple[list[list[str]], list[list[float]], dict[str, float]]:
    """The exact top-``depth`` neighbours per query, their scores, and the cost.

    Scores are kept, not just ids: this corpus contains genuinely
    equal-scoring chunks — boilerplate repeated verbatim across filings — and
    without the scores there is no way to tell a copy that holds different
    vectors from one that broke a tie differently. See
    :func:`compare_exact_lists`.

    The latency is reported as a real arm of the curve, not as overhead: brute
    force *is* an operating point — the one with recall 1.0 by definition —
    and a curve that hides its price cannot show what the graph is buying.
    """
    lists: list[list[str]] = []
    scores: list[list[float]] = []
    per_query_ms: list[float] = []
    for vector in vectors:
        started = time.perf_counter()
        hits = exact_knn_search(client, index_name, vector, k=depth)
        per_query_ms.append((time.perf_counter() - started) * 1000)
        lists.append([hit["chunk_id"] for hit in hits])
        scores.append([float(hit["score"]) for hit in hits])
    return lists, scores, latency_summary(per_query_ms)


def index_size_stats(client, index_name: str, *, timeout: float = 60.0) -> dict[str, int]:
    """How big the index is, counting the segments it actually has.

    Summed from the segments API rather than taken from ``_stats``'s
    ``store.size_in_bytes``. Store size measures the *directory*, and a force
    merge writes the new segment before the superseded ones are unlinked, so
    the directory can hold two copies of the corpus at once: this sweep's
    first run recorded 774 MB for a one-segment index that holds 358 MB of
    live segment. Both are reported — ``store_size_bytes`` beside
    ``size_bytes`` — so the gap is inspectable rather than something a reader
    has to take on trust.

    Polled until two consecutive readings agree, because a merge that is
    still committing can also be caught mid-write and read *low*. ``settled``
    records whether it converged; a size reported after the timeout is a
    statement about when it was read.
    """
    previous: int | None = None
    deadline = time.perf_counter() + timeout
    while True:
        client.indices.refresh(index=index_name)
        shards = client.indices.segments(index=index_name)["indices"][index_name]["shards"]
        segments = [
            segment
            for shard in shards.values()
            for copy in shard
            for segment in copy["segments"].values()
        ]
        size = sum(int(segment["size_in_bytes"]) for segment in segments)
        settled = size == previous
        if settled or time.perf_counter() > deadline:
            store = client.indices.stats(index=index_name, metric="store")["indices"][index_name][
                "primaries"
            ]["store"]["size_in_bytes"]
            return {
                "size_bytes": size,
                "store_size_bytes": int(store),
                "segments": len(segments),
                "size_settled": settled,
            }
        previous = size
        time.sleep(2.0)


def build_sweep_index(
    *, client, source_index: str, target_index: str, config: BuildConfig, expected_documents: int
) -> dict[str, Any]:
    """Copy the corpus's vectors into a fresh index built at ``config``.

    ``_reindex`` moves the stored vectors as they are, so the embedding model
    is never re-run: re-embedding 38,483 chunks to answer a question about
    graph parameters would cost about ten minutes and, on this machine, risk
    the swap collapse that took an earlier index build from 80 chunks/s to 3.

    Only ``chunk_id`` and ``embedding`` are copied. Nothing in this sweep reads
    the text, and carrying it would triple the disk each configuration holds.
    Force-merged to a single segment afterwards because segment count changes
    both recall and latency on its own — every copy has to differ from every
    other copy in the swept parameters and nothing else.
    """
    if not target_index.startswith(SWEEP_PREFIX):
        raise ValueError(
            f"refusing to build {target_index!r}: sweep indexes must be namespaced "
            f"under {SWEEP_PREFIX!r} so cleanup cannot reach a served index."
        )
    if client.indices.exists(index=target_index):
        client.indices.delete(index=target_index)

    mapping = build_index_mapping(m=config.m, ef_construction=config.ef_construction)
    properties = mapping["mappings"]["properties"]
    mapping["mappings"]["properties"] = {
        "chunk_id": properties["chunk_id"],
        "embedding": properties["embedding"],
    }
    # No periodic refresh during the copy, for the same reason build_index.py
    # suspends it: each refresh cuts a segment, and every new segment of a
    # k-NN index means another HNSW graph built over data still arriving.
    mapping["settings"]["index"]["refresh_interval"] = "-1"
    client.indices.create(index=target_index, body=mapping)

    started = time.perf_counter()
    client.reindex(
        body={
            "source": {"index": source_index, "_source": ["chunk_id", "embedding"], "size": 1000},
            "dest": {"index": target_index},
        },
        refresh=True,
        wait_for_completion=True,
        request_timeout=3600,
    )
    reindex_seconds = time.perf_counter() - started

    started = time.perf_counter()
    client.indices.forcemerge(index=target_index, max_num_segments=1, request_timeout=3600)
    merge_seconds = time.perf_counter() - started
    client.indices.flush(index=target_index)
    client.indices.refresh(index=target_index)

    documents = document_count(client, target_index)
    if documents != expected_documents:
        raise RuntimeError(
            f"{target_index} holds {documents} documents but {source_index} holds "
            f"{expected_documents}: a partial copy scores a smaller corpus and "
            "reports it as a recall difference."
        )

    return {
        "m": config.m,
        "ef_construction": config.ef_construction,
        "documents": documents,
        "reindex_seconds": reindex_seconds,
        "forcemerge_seconds": merge_seconds,
        "build_seconds": reindex_seconds + merge_seconds,
        **index_size_stats(client, target_index),
    }


def compare_exact_lists(
    source_ids: list[str],
    source_scores: list[float],
    copy_ids: list[str],
    copy_scores: list[float],
    *,
    tolerance: float = 1e-6,
) -> str:
    """Classify one query's copy-versus-source exact ranking.

    ``"identical"``, ``"tied"`` (the difference is only between documents the
    corpus scores equally), or ``"different"`` (the copy holds different
    vectors, which would invalidate every measurement taken against it).

    The distinction is not pedantry — it is the difference between a copying
    bug and a fact about the corpus. Order among equal scores follows Lucene's
    internal document ids, which a seven-segment index and a force-merged
    one-segment copy do not share, so a faithful copy still reorders ties. And
    where a tie straddles the ``k``-th place, which of the tied documents makes
    the cut is arbitrary in both.
    """
    if source_ids == copy_ids:
        return "identical"

    source_by_id = dict(zip(source_ids, source_scores, strict=True))
    copy_by_id = dict(zip(copy_ids, copy_scores, strict=True))

    if set(source_ids) == set(copy_ids):
        # Same documents, different order. Faithful only if every position
        # they disagree at holds equally-scoring documents.
        return (
            "tied"
            if all(
                abs(source_by_id[a] - copy_by_id[b]) <= tolerance
                for a, b in zip(source_ids, copy_ids, strict=True)
            )
            else "different"
        )

    # Different documents. Faithful only if the newcomers and the dropped
    # both score at the cut — a tie the k-th place happens to fall inside.
    cut = min(source_scores)
    for chunk_id in set(source_ids) ^ set(copy_ids):
        score = source_by_id.get(chunk_id, copy_by_id.get(chunk_id))
        if score is None or abs(score - cut) > tolerance:
            return "different"
    return "tied"


def verify_copy_vectors(
    *,
    client,
    index_name: str,
    vectors: list[list[float]],
    ground_truth: list[list[str]],
    ground_truth_scores: list[list[float]],
    depth: int,
) -> dict[str, Any]:
    """Check that the copy holds the source's vectors, by exact search on both.

    A ``_reindex`` round-trips every vector through JSON. If that lost
    precision the copy would still answer every query — from a slightly
    different neighbourhood, which would surface in this report as a
    build-parameter effect that is really a copying artefact. Exact search
    consults no graph, so this compares the vectors and nothing else.

    ``different`` is the only count that means a problem; ``tied`` is a fact
    about the corpus (see :func:`compare_exact_lists`) and is reported rather
    than folded into either of the other two.
    """
    verdicts = {"identical": 0, "tied": 0, "different": 0}
    differing: list[int] = []
    for index, (vector, exact, scores) in enumerate(
        zip(vectors, ground_truth, ground_truth_scores, strict=True)
    ):
        hits = exact_knn_search(client, index_name, vector, k=depth)
        verdict = compare_exact_lists(
            exact,
            scores,
            [hit["chunk_id"] for hit in hits],
            [float(hit["score"]) for hit in hits],
        )
        verdicts[verdict] += 1
        if verdict == "different":
            differing.append(index)
    return {
        "queries": len(vectors),
        **verdicts,
        "queries_with_different_vectors": differing,
        "vectors_match_source": not differing,
    }


def measure_served_pipeline(
    *,
    client,
    index_name: str,
    entries: list[dict],
    vectors: list[list[float]],
    reranker,
    candidate_k: int,
    ef_search: int | None,
    k: int,
) -> dict[str, Any]:
    """The whole served path — RRF fusion plus cross-encoder — at one ef_search.

    Here because a dense-path number alone describes a configuration nobody
    runs. This repository has already measured a +0.233 dense recall@10 gain
    arriving at the user as +0.000 through this same pipeline; an ANN change
    has to be quoted through it too, in whichever direction it lands.
    """
    per_query_ms: list[float] = []
    reranked: list[list[str]] = []
    for entry, vector in zip(entries, vectors, strict=True):
        started = time.perf_counter()
        candidates = hybrid_search(
            client,
            index_name,
            entry["question"],
            vector,
            k=candidate_k,
            candidate_k=candidate_k,
            ef_search=ef_search,
        )
        hits = reranker.rerank(entry["question"], candidates, top_k=k)
        per_query_ms.append((time.perf_counter() - started) * 1000)
        reranked.append([hit["chunk_id"] for hit in hits])

    return {
        "ef_search": ef_search,
        "candidate_k": candidate_k,
        "latency_ms": latency_summary(per_query_ms),
        "retrieval": aggregate_metrics(
            [
                (hits, set(entry["relevant_chunk_ids"]))
                for hits, entry in zip(reranked, entries, strict=True)
            ],
            k_values=_METRIC_K,
        ),
        "_reranked": reranked,
    }


def _print_curve(title: str, points: list[dict[str, Any]], exact_ms: float | None = None) -> None:
    print(f"\n{title}")
    header = (
        f"{'ef_search':>10}{'ann recall':>12}{'worst q':>9}{'exact lists':>13}"
        f"{'p50 ms':>9}{'p95 ms':>9}{'dense r@10':>12}"
    )
    print(header)
    print("-" * len(header))
    for point in points:
        label = "default" if point["ef_search"] is None else str(point["ef_search"])
        print(
            f"{label:>10}"
            f"{point['ann_recall']:>12.4f}"
            f"{point['ann_recall_min']:>9.2f}"
            f"{point['queries_matching_exact_exactly']:>13d}"
            f"{point['latency_ms']['p50']:>9.1f}"
            f"{point['latency_ms']['p95']:>9.1f}"
            f"{point['retrieval'][_HEADLINE_METRIC]:>12.3f}"
        )
    if exact_ms is not None:
        print(f"{'exact':>10}{1.0:>12.4f}{1.0:>9.2f}{'—':>13}{'—':>9}{exact_ms:>9.1f}")


def _print_build_sweep(rows: list[dict[str, Any]], k: int, ef_max: int | None) -> None:
    print(f"\nbuild sweep (one-segment vector-only copies), k={k}")
    header = (
        f"{'build':>12}{'build s':>9}{'MB':>7}{'ann@default':>13}"
        f"{'ann@ef' + str(ef_max):>13}{'p95 default':>13}{'dense r@10':>12}"
    )
    print(header)
    print("-" * len(header))
    for row in rows:
        points = [p for p in row["points"] if p["k"] == k]
        default = next(p for p in points if p["ef_search"] is None)
        widened = next(p for p in points if p["ef_search"] == ef_max)
        print(
            f"{row['label']:>12}"
            f"{row['config']['build_seconds']:>9.1f}"
            f"{row['config']['size_bytes'] / 1e6:>7.0f}"
            f"{default['ann_recall']:>13.4f}"
            f"{widened['ann_recall']:>13.4f}"
            f"{default['latency_ms']['p95']:>13.1f}"
            f"{default['retrieval'][_HEADLINE_METRIC]:>12.3f}"
        )
    print(
        "  One build per cell. HNSW construction is randomised, and rebuilding one "
        "cell twice moved ANN recall by 0.084 — wider than these cells differ, so "
        "read this as a range the parameters live in, not a ranking of them."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        default="finetuned",
        help="config profile naming the model and index (default: the fine-tuned pair)",
    )
    parser.add_argument("--eval-set", default=DEFAULT_EVAL_SET_PATH)
    parser.add_argument("--split", choices=SPLITS, default=None)
    parser.add_argument(
        "--k-values",
        default=",".join(str(k) for k in DEFAULT_K_VALUES),
        help="retrieval depths to sweep at (default: the dense eval's 10 and the pipeline's 50)",
    )
    parser.add_argument("--ef-search", default=",".join(str(v) for v in DEFAULT_EF_SEARCH))
    parser.add_argument("--m", default=",".join(str(v) for v in DEFAULT_M_VALUES))
    parser.add_argument(
        "--ef-construction", default=",".join(str(v) for v in DEFAULT_EF_CONSTRUCTION_VALUES)
    )
    parser.add_argument("--repeats", type=int, default=3, help="timed passes over the question set")
    parser.add_argument("--target-ann-recall", type=float, default=DEFAULT_TARGET_ANN_RECALL)
    parser.add_argument(
        "--skip-build-sweep",
        action="store_true",
        help="measure only ef_search on the served index — no index is created or deleted",
    )
    parser.add_argument(
        "--keep-indexes",
        action="store_true",
        help="leave the swept copies in place (each holds the full corpus's vectors)",
    )
    parser.add_argument(
        "--rerank",
        action="store_true",
        help=(
            "also measure the chosen operating point through the served pipeline "
            "(RRF + cross-encoder), which is the only arm that says what a user sees"
        ),
    )
    parser.add_argument("--out", default=DEFAULT_REPORT)
    parser.add_argument("--run-name", default=RUN_NAME)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    config = load_config(profile=args.profile)
    model_name = config.models.embedding_model
    index_name = config.opensearch.index_name
    client = build_client(config.opensearch)

    entries = load_eval_set(args.eval_set, split=args.split)
    k_values = sorted(int(value) for value in args.k_values.split(",") if value.strip())
    ef_values = [int(value) for value in args.ef_search.split(",") if value.strip()]
    depth = max(k_values)

    embedder = ChunkEmbedder(model_name)
    vectors = [vector.tolist() for vector in embedder.embed_queries([e["question"] for e in entries])]
    documents = document_count(client, index_name)
    logger.info("%d questions, %d indexed documents, ground truth at depth %d",
                len(entries), documents, depth)

    started = time.perf_counter()
    ground_truth, ground_truth_scores, exact_latency = exact_ground_truth(
        client=client, index_name=index_name, vectors=vectors, depth=depth
    )
    logger.info("exact ground truth in %.1f s (%.1f ms/query)",
                time.perf_counter() - started, exact_latency["mean"])

    served_stats = index_size_stats(client, index_name)

    served_curve: dict[int, list[dict[str, Any]]] = {}
    operating_points: dict[int, dict[str, Any]] = {}
    justifications: list[str] = []
    for k in k_values:
        points = []
        for ef_search in search_points(ef_values, k):
            logger.info("served index: k=%d ef_search=%s", k, ef_search)
            points.append(
                measure_point(
                    client=client,
                    index_name=index_name,
                    build_label="served",
                    entries=entries,
                    vectors=vectors,
                    ground_truth=ground_truth,
                    k=k,
                    ef_search=ef_search,
                    repeats=args.repeats,
                )
            )
        served_curve[k] = points
        chosen, reached = choose_operating_point(points, target=args.target_ann_recall)
        baseline = next(point for point in points if point["ef_search"] is None)
        operating_points[k] = {
            "ef_search": chosen["ef_search"],
            "reached_target": reached,
            "ann_recall": chosen["ann_recall"],
            "latency_ms": chosen["latency_ms"],
            "retrieval": chosen["retrieval"],
            "default_ann_recall": baseline["ann_recall"],
            "default_latency_ms": baseline["latency_ms"],
        }
        justifications.append(
            justification(chosen, baseline, reached=reached, target=args.target_ann_recall)
        )
        _print_curve(f"served index {index_name}, k={k}", points, exact_ms=exact_latency["p50"])

    build_rows: list[dict[str, Any]] = []
    if not args.skip_build_sweep:
        grid = build_grid(
            [int(v) for v in args.m.split(",") if v.strip()],
            [int(v) for v in args.ef_construction.split(",") if v.strip()],
        )
        for build_config in grid:
            target_index = sweep_index_name(index_name, build_config)
            logger.info("building %s", target_index)
            built = build_sweep_index(
                client=client,
                source_index=index_name,
                target_index=target_index,
                config=build_config,
                expected_documents=documents,
            )
            try:
                verified = verify_copy_vectors(
                    client=client,
                    index_name=target_index,
                    vectors=vectors,
                    ground_truth=ground_truth,
                    ground_truth_scores=ground_truth_scores,
                    depth=depth,
                )
                points = [
                    measure_point(
                        client=client,
                        index_name=target_index,
                        build_label=build_config.label,
                        entries=entries,
                        vectors=vectors,
                        ground_truth=ground_truth,
                        k=k,
                        ef_search=ef_search,
                        repeats=args.repeats,
                    )
                    for k in k_values
                    for ef_search in search_points(ef_values, k)
                ]
            finally:
                if not args.keep_indexes:
                    client.indices.delete(index=target_index)
            build_rows.append(
                {
                    "label": build_config.label,
                    "config": built,
                    "vector_check": verified,
                    "points": points,
                }
            )
        widest = search_points(ef_values, max(k_values))[-1]
        for k in k_values:
            _print_build_sweep(build_rows, k, widest)

    served_pipeline = None
    if args.rerank:
        from duediligence.index.rerank import CrossEncoderReranker

        reranker = CrossEncoderReranker(config.models.reranker_model)
        candidate_k = max(k_values)
        arms = []
        for ef_search in dict.fromkeys([None, operating_points[candidate_k]["ef_search"]]):
            logger.info("served pipeline: ef_search=%s", ef_search)
            arms.append(
                measure_served_pipeline(
                    client=client,
                    index_name=index_name,
                    entries=entries,
                    vectors=vectors,
                    reranker=reranker,
                    candidate_k=candidate_k,
                    ef_search=ef_search,
                    k=10,
                )
            )
        identical = (
            sum(1 for a, b in zip(arms[0]["_reranked"], arms[-1]["_reranked"], strict=True) if a == b)
        )
        served_pipeline = {
            "arms": [{k: v for k, v in arm.items() if not k.startswith("_")} for arm in arms],
            "identical_reranked_lists": identical,
            "delta": {
                metric: round(
                    arms[-1]["retrieval"][metric] - arms[0]["retrieval"][metric], 4
                )
                for metric in arms[0]["retrieval"]
            },
        }

    report = {
        "model": model_name,
        "profile": args.profile,
        "index": index_name,
        "eval_set": args.eval_set,
        "split": args.split or "all",
        "queries": len(entries),
        "human_verified": human_verified_count(entries),
        "indexed_documents": documents,
        "repeats": args.repeats,
        "target_ann_recall": args.target_ann_recall,
        "ground_truth": {
            "method": "match_all + knn_score painless script (brute force, no HNSW graph)",
            "depth": depth,
            "latency_ms": exact_latency,
            "retrieval_by_k": {
                str(k): aggregate_metrics(
                    [
                        (exact[:k], set(entry["relevant_chunk_ids"]))
                        for exact, entry in zip(ground_truth, entries, strict=True)
                    ],
                    k_values=_METRIC_K,
                )
                for k in k_values
            },
        },
        "served_index": {
            "build": {"m": DEFAULT_M, "ef_construction": DEFAULT_EF_CONSTRUCTION},
            "segments": served_stats["segments"],
            "size_bytes": served_stats["size_bytes"],
            "store_size_bytes": served_stats["store_size_bytes"],
            "curve": {str(k): points for k, points in served_curve.items()},
        },
        "operating_point": {str(k): point for k, point in operating_points.items()},
        "justification": justifications,
        "build_sweep": build_rows,
        # One boolean over the whole grid: every copy answered exact search
        # with the source's own neighbourhoods, so the differences below are
        # the swept parameters rather than a lossy copy.
        "build_sweep_vectors_verified": all(
            row["vector_check"]["vectors_match_source"] for row in build_rows
        )
        if build_rows
        else None,
        "served_pipeline": served_pipeline,
        "caveats": [
            "Latencies are wall-clock at the client over HTTP to a local container on an "
            "8 GB Mac; quote the ratios between points, not the absolute milliseconds.",
            "The build sweep runs on one-segment, vector-only copies made with _reindex. "
            "They are comparable to each other and not to the served index, which has "
            f"{served_stats['segments']} segments and carries the text field.",
            "ANN recall is measured against exact search over the same vectors. It says "
            "how much of the true neighbourhood the graph reached, not whether that "
            "neighbourhood answers the question — which is what the labelled metrics "
            "beside it are for.",
            "Relevance labels are a lower bound (mean 1.02 labelled chunks per question), "
            "so absolute end-task recall understates every point equally.",
            "This corpus contains equal-scoring chunks (boilerplate repeated verbatim "
            "across filings), so where a tie straddles the k-th place the 'true' top k "
            "is itself arbitrary. ANN recall therefore understates slightly: a graph "
            "that returned the other member of a tie is counted as having missed.",
        ],
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n")

    print()
    for sentence in justifications:
        print(f"  {sentence}")
    print(f"\nwrote {out_path}")

    url = log_run(
        name=args.run_name,
        config={
            "model": model_name,
            "index": index_name,
            "profile": args.profile,
            "split": report["split"],
            "k_values": k_values,
            "ef_search": ef_values,
            "repeats": args.repeats,
        },
        metrics=flatten_metrics(report),
        tags=["ann", "hnsw", "latency", "vector-search"],
        notes="HNSW recall-versus-latency curve: ef_search on the served index, "
        "m/ef_construction on rebuilt copies.",
    )
    if url:
        print(f"tracked: {url}")


if __name__ == "__main__":
    main()
