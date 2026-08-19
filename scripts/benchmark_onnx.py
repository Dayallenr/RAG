"""Benchmark the ONNX and INT8 backends against PyTorch — speed *and* recall.

An inference-optimisation report that quotes only a speedup is half a
measurement. Quantisation changes the arithmetic, so it changes the vectors,
so it can change what comes back from the index; the interesting number is
what that costs. This runs all three backends over the same eval set, the same
index and the same corpus sample, and reports latency, throughput, vector
fidelity and dense retrieval quality side by side.

Two comparisons are deliberately kept apart. **Runtime versus hardware**: the
PyTorch baseline runs on the fastest local device (MPS here) and the ONNX
backends run on CPU, so a `torch:cpu` arm is measured alongside them —
without it, "ONNX is faster" and "CPU is faster at batch 1" are the same
number. **Dense versus served**: recall is scored both on the raw dense k-NN
path, where a vector change shows up undamped, and through the pipeline this
project actually serves (RRF + cross-encoder rerank), where this repository has
already established that a large dense gain reaches the user as +0.000. A
degradation quoted only on the dense path describes a configuration nobody
runs — the same mistake in the opposite direction.

**What is being measured, exactly.** The quantised model is swapped in as the
*query* encoder against an index whose vectors were produced by the PyTorch
model. That is the deployment a service can reach by setting one environment
variable, and it is the one measured here. Re-embedding all 38,483 chunks with
the quantised model would measure a different (and more expensive) deployment;
it is not measured, and no number here should be read as covering it. Passage
throughput and passage-side fidelity *are* measured, so the cost of that
re-index is visible even though the re-index was not run.

Latency figures are machine-dependent — this is an 8 GB Mac that swaps under
load (see docs/engineering-notes.md). Quote the ratios between backends, not
the absolute milliseconds.

Usage:
    python scripts/benchmark_onnx.py --profile finetuned
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.config import load_config  # noqa: E402
from duediligence.eval.eval_set import (  # noqa: E402
    DEFAULT_EVAL_SET_PATH,
    SPLITS,
    load_eval_set,
)
from duediligence.eval.retrieval_metrics import aggregate_metrics  # noqa: E402
from duediligence.index.embed import BACKENDS, ChunkEmbedder  # noqa: E402
from duediligence.index.hybrid_search import hybrid_search  # noqa: E402
from duediligence.index.onnx_embed import onnx_export_dir  # noqa: E402
from duediligence.index.opensearch_client import build_client, knn_search  # noqa: E402
from duediligence.track import flatten_metrics, log_run  # noqa: E402

logger = logging.getLogger("benchmark-onnx")

DEFAULT_REPORT = "results/onnx/report.json"
RUN_NAME = "onnx-benchmark"

#: The arm every other report in this repository was produced with, and
#: therefore the one the others are scored against.
BASELINE_ARM = "torch"

#: Fusion settings the served pipeline uses, copied from
#: ``duediligence/pipeline.py`` so the reranked arm scores the configuration
#: this project actually deploys rather than a more favourable one.
_CANDIDATE_K = 50

#: Metrics the degradation table covers: the five the retrieval eval and the
#: fine-tune delta report, so the three tables can be read together, plus
#: recall@20. recall@20 is here because on the first real run it was the *only*
#: metric INT8 moved — a table without it reported "zero change on every
#: metric" for a backend whose result lists differed on all 101 questions.
_REPORTED_METRICS = ("recall@1", "recall@5", "recall@10", "recall@20", "mrr", "ndcg@10")

_K_VALUES = (1, 3, 5, 10, 20)


@dataclass(frozen=True)
class Arm:
    """One measured configuration: a backend, and the device it runs on.

    ``torch`` and ``torch:cpu`` are the same weights and the same code on
    different hardware, so they need distinct labels rather than distinct
    backends. The label is what every delta and every report key is keyed on.
    """

    label: str
    backend: str
    device: str | None


def parse_arm(spec: str) -> Arm:
    """``"onnx-int8"`` or ``"torch:cpu"`` into an :class:`Arm`.

    A device may only be pinned on the PyTorch backend: the ONNX sessions here
    are built with the CPU execution provider, so accepting ``onnx:cuda`` would
    label a measurement with hardware it did not use.
    """
    label = spec.strip()
    backend, _, device = label.partition(":")
    if device and backend != "torch":
        raise ValueError(
            f"cannot pin a device on backend {backend!r} ({label!r}): the ONNX "
            "sessions run on the CPU execution provider, and labelling a run "
            "with hardware it did not use is worse than not measuring it."
        )
    return Arm(label=label, backend=backend, device=device or None)


def percentile(values: list[float], fraction: float) -> float:
    """Nearest-rank percentile. Small samples here (101 queries), so no
    interpolation: an interpolated p95 of 101 samples invents a number that
    no single query produced."""
    if not values:
        raise ValueError("no values to take a percentile of")
    ordered = sorted(values)
    rank = max(1, min(len(ordered), int(round(fraction * len(ordered)))))
    return ordered[rank - 1]


def degradation(baseline: dict[str, float], variant: dict[str, float]) -> dict[str, float]:
    """Variant minus baseline, per metric. Negative is a loss.

    Signed and in the metric's own units rather than a percentage: a recall@10
    of 0.600 dropping to 0.590 is -0.010, which is one question in sixty, and
    "-1.7%" hides that.
    """
    return {
        metric: round(variant[metric] - baseline[metric], 4)
        for metric in _REPORTED_METRICS
        if metric in baseline and metric in variant
    }


def speedup(baseline_ms: float, variant_ms: float) -> float:
    """How many times faster the variant is. >1 is faster."""
    return round(baseline_ms / variant_ms, 3) if variant_ms else float("inf")


def trade_off_sentence(name: str, summary: dict, *, queries: int, k: int) -> str:
    """State the trade-off in one sentence, from the numbers just measured.

    Built from the report rather than written by hand so it cannot survive a
    re-run that changes the result — a stale "2x faster at no cost" sentence
    beside a table showing otherwise is exactly the failure this project's
    prime directive exists to prevent.
    """
    query_speedup = summary["query_latency_speedup_vs_torch"]
    recall_delta = summary["retrieval_delta_vs_torch"].get("recall@10")
    size_ratio = summary["size_ratio_vs_torch"]
    identical = summary["identical_result_lists_vs_torch"]
    faster = f"{query_speedup:.2f}x" if query_speedup >= 1 else f"{1 / query_speedup:.2f}x slower"
    direction = "faster" if query_speedup >= 1 else ""
    cost = "no change in dense recall@10" if recall_delta == 0 else f"{recall_delta:+.3f} dense recall@10"
    # A model whose weights live in a shared Hub cache has no file in this
    # repository to size, and printing "0.00x the on-disk size" for it would
    # read as a measurement rather than as an absence.
    size = f"{size_ratio:.2f}x the on-disk size" if size_ratio else "on-disk size not comparable"

    # An unchanged metric is not an unchanged result. A backend can reorder
    # every result list and still score identically, because recall@k only
    # asks whether the labelled chunk is in the top k — so the two facts are
    # reported in the same breath rather than leaving a reader to infer one
    # from the other.
    differing = queries - identical
    if differing == 0:
        ordering = f" Dense result lists are identical on all {queries} questions."
    else:
        ordering = f" The dense top-{k} lists differ on {differing} of {queries} questions"
        # Only say the results moved while the metrics did not when that is
        # what happened — appending it to a run whose recall *did* move would
        # contradict the same sentence's own first half.
        ordering += (
            ", so the metrics are unchanged rather than the results."
            if recall_delta == 0
            else "."
        )

    served = summary.get("reranked_delta_vs_torch")
    if served is not None:
        reranked_delta = served.get("recall@10")
        same = summary["identical_reranked_lists_vs_torch"]
        ordering += (
            f" Through the served pipeline (RRF + cross-encoder) it is "
            f"{reranked_delta:+.3f} recall@10 with {same} of {queries} reranked lists "
            "identical."
        )
    return (
        f"{name}: single-query encoding {faster} {direction}".rstrip()
        + f", {size}, for {cost}."
        + ordering
    )


def _model_size_bytes(model_name: str, backend: str) -> int | None:
    """Bytes on disk for the artifact this backend actually loads.

    ``None`` when there is no file here to measure — a Hub id resolves out of
    a shared cache, and reporting that as 0 bytes would be a measurement of
    something that was never weighed.
    """
    if backend == "torch":
        directory = Path(model_name)
        if not directory.is_dir():
            return None
        return sum(p.stat().st_size for p in directory.glob("*.safetensors"))
    from duediligence.index.onnx_embed import INT8_MODEL_FILENAME, ONNX_MODEL_FILENAME

    filename = INT8_MODEL_FILENAME if backend == "onnx-int8" else ONNX_MODEL_FILENAME
    return (onnx_export_dir(model_name) / filename).stat().st_size


def load_passage_sample(chunks_dir: str, limit: int) -> list[str]:
    """Real corpus text for the throughput measurement.

    Real chunks rather than synthetic strings: throughput is dominated by
    sequence length, so a sample of uniform short strings would measure a
    corpus this project does not have. Taken in file order rather than
    sampled at random so two runs are comparable.
    """
    texts: list[str] = []
    for path in sorted(Path(chunks_dir).glob("*.jsonl")):
        with path.open() as handle:
            for line in handle:
                texts.append(json.loads(line)["text"])
                if len(texts) >= limit:
                    return texts
    return texts


def contract_check(embedder: ChunkEmbedder, texts: list[str]) -> dict:
    """The interface contract, measured rather than assumed, on this backend.

    Three properties the index depends on and none of which fail loudly:
    the dimension the mapping is built for, unit-norm vectors for a cosine
    field, and query/passage encoding staying distinct — a backend that
    dropped BGE's query prefix would retrieve worse and raise nothing.
    """
    queries = embedder.embed_queries(texts)
    passages = embedder.embed_passages(texts)
    cross = [float(q @ p) for q, p in zip(queries, passages, strict=True)]
    norms = np.concatenate(
        [np.linalg.norm(queries, axis=1), np.linalg.norm(passages, axis=1)]
    )
    return {
        "dimension": int(queries.shape[1]),
        "max_norm_error": float(np.abs(norms - 1.0).max()),
        "query_passage_max_cosine": max(cross),
        "query_and_passage_encoding_distinct": max(cross) < 0.999,
    }


def measure_arm(
    *,
    arm: Arm,
    model_name: str,
    questions: list[str],
    passages: list[str],
    client,
    index_name: str,
    entries: list[dict],
    k: int,
    batch_size: int,
    reranker=None,
) -> dict:
    """Everything measured for one arm, against one index.

    ``reranker`` is passed in rather than constructed here so the
    cross-encoder is loaded once for the whole run: this is an 8 GB machine
    that swaps, and one resident copy per arm is how an earlier index build
    degraded from 80 chunks/s to 3.
    """
    embedder = ChunkEmbedder(
        model_name, backend=arm.backend, device=arm.device, batch_size=batch_size
    )

    # Warm up before timing anything. The first encode after process start is
    # kernel/session warmup, not steady state — a traced /ask on this machine
    # once recorded 1,867 ms for an embedding step whose steady state is tens
    # of milliseconds.
    embedder.embed_queries(questions[:8])
    embedder.embed_passages(passages[:8])

    per_query_ms: list[float] = []
    query_vectors = []
    for question in questions:
        started = time.perf_counter()
        vector = embedder.embed_query(question)
        per_query_ms.append((time.perf_counter() - started) * 1000)
        query_vectors.append(vector)

    started = time.perf_counter()
    passage_vectors = embedder.embed_passages(passages)
    passage_seconds = time.perf_counter() - started

    def _score(result_lists: list[list[str]]) -> dict[str, float]:
        return aggregate_metrics(
            [
                (hits, set(entry["relevant_chunk_ids"]))
                for hits, entry in zip(result_lists, entries, strict=True)
            ],
            k_values=_K_VALUES,
        )

    retrieved = [
        [hit["chunk_id"] for hit in knn_search(client, index_name, vector, k=k)]
        for vector in query_vectors
    ]

    measured = {
        "backend": arm.backend,
        "device": embedder.device,
        "loaded": embedder.describe,
        "size_bytes": _model_size_bytes(model_name, arm.backend),
        "query_latency_ms": {
            "mean": sum(per_query_ms) / len(per_query_ms),
            "p50": percentile(per_query_ms, 0.50),
            "p95": percentile(per_query_ms, 0.95),
            "queries": len(per_query_ms),
        },
        "passage_throughput": {
            "texts": len(passages),
            "seconds": passage_seconds,
            "texts_per_second": len(passages) / passage_seconds,
            "batch_size": batch_size,
        },
        "contract": contract_check(embedder, questions[:8]),
        "retrieval": _score(retrieved),
        # Kept, not just scored: the fidelity comparison against PyTorch is
        # computed from these, and the per-query result lists are what make a
        # zero delta checkable rather than merely reported.
        "_query_vectors": np.asarray(query_vectors, dtype=np.float32),
        "_passage_vectors": passage_vectors,
        "_retrieved": retrieved,
    }

    if reranker is not None:
        # The served path, at the pipeline's own fusion settings: a
        # degradation quoted only on the dense path describes a configuration
        # nobody runs, which is the same error as quoting the fine-tune's
        # dense-only gain (see the fine-tune section of the README).
        started = time.perf_counter()
        reranked = []
        for entry, vector in zip(entries, query_vectors, strict=True):
            candidates = hybrid_search(
                client,
                index_name,
                entry["question"],
                vector,
                k=_CANDIDATE_K,
                candidate_k=_CANDIDATE_K,
            )
            reranked.append(
                [hit["chunk_id"] for hit in reranker.rerank(entry["question"], candidates, top_k=k)]
            )
        measured["reranked_latency_ms_mean"] = (
            (time.perf_counter() - started) * 1000 / len(entries)
        )
        measured["reranked_retrieval"] = _score(reranked)
        measured["_reranked"] = reranked

    return measured


def fidelity(baseline: dict, variant: dict) -> dict:
    """How close the variant's vectors are to the baseline's, both sides.

    Cosine rather than max absolute difference: the vectors are unit-norm and
    the index scores them by cosine, so this is the deviation in the units
    retrieval actually uses.
    """
    result = {}
    for side in ("query", "passage"):
        reference = baseline[f"_{side}_vectors"]
        actual = variant[f"_{side}_vectors"]
        cosines = np.sum(actual * reference, axis=1)
        result[side] = {"mean_cosine": float(cosines.mean()), "min_cosine": float(cosines.min())}
    return result


def identical_result_lists(baseline: dict, variant: dict, key: str = "_retrieved") -> int:
    """Questions whose top-k list is identical, in order, to the baseline's.

    Reported alongside the metric deltas because they answer different
    questions: a delta of 0.000 can mean "the same results" or "different
    results that score the same", and only one of those is a null effect.
    """
    return sum(1 for a, b in zip(baseline[key], variant[key], strict=True) if a == b)


def build_report(
    *,
    measurements: dict[str, dict],
    model_name: str,
    profile: str | None,
    index_name: str,
    eval_set_path: str,
    split: str | None,
    entries: list[dict],
    k: int,
    export_report: dict | None,
) -> dict:
    baseline = measurements[BASELINE_ARM]
    arms: dict[str, dict] = {}
    for name, measured in measurements.items():
        summary = {key: value for key, value in measured.items() if not key.startswith("_")}
        summary["query_latency_speedup_vs_torch"] = speedup(
            baseline["query_latency_ms"]["mean"], measured["query_latency_ms"]["mean"]
        )
        summary["throughput_speedup_vs_torch"] = round(
            measured["passage_throughput"]["texts_per_second"]
            / baseline["passage_throughput"]["texts_per_second"],
            3,
        )
        summary["size_ratio_vs_torch"] = (
            round(measured["size_bytes"] / baseline["size_bytes"], 3)
            if measured["size_bytes"] and baseline["size_bytes"]
            else None
        )
        summary["retrieval_delta_vs_torch"] = degradation(
            baseline["retrieval"], measured["retrieval"]
        )
        summary["vector_fidelity_vs_torch"] = fidelity(baseline, measured)
        summary["identical_result_lists_vs_torch"] = identical_result_lists(baseline, measured)
        if "reranked_retrieval" in measured:
            summary["reranked_delta_vs_torch"] = degradation(
                baseline["reranked_retrieval"], measured["reranked_retrieval"]
            )
            summary["identical_reranked_lists_vs_torch"] = identical_result_lists(
                baseline, measured, key="_reranked"
            )
        arms[name] = summary

    return {
        "model": model_name,
        "profile": profile,
        "index": index_name,
        # The index was built by the PyTorch model. Every arm below is
        # measured as a *query* encoder against those vectors, which is the
        # deployment one environment variable can reach. Re-embedding the
        # corpus with a quantised model is a different deployment and was not
        # run — see the module docstring.
        "index_built_with_backend": "torch",
        "eval_set": eval_set_path,
        "split": split or "all",
        "queries": len(entries),
        "k": k,
        "candidate_k": _CANDIDATE_K,
        "baseline_arm": BASELINE_ARM,
        "export": export_report,
        "backends": arms,
        "trade_off": [
            trade_off_sentence(name, summary, queries=len(entries), k=k)
            for name, summary in arms.items()
            if name != BASELINE_ARM
        ],
        "caveats": [
            "Latencies are machine-dependent (8 GB Mac, CPU-contention-sensitive); "
            "quote the ratios between arms, not the absolute milliseconds.",
            "The ONNX backends run on CPU. The PyTorch baseline runs on the fastest "
            "local device, which here is MPS, so a torch:cpu arm is measured "
            "alongside it — otherwise 'ONNX is faster' and 'CPU is faster at batch "
            "1' would be the same number.",
            "Recall is measured with each backend as the query encoder against an "
            "index built by the PyTorch model. Re-embedding the corpus with a "
            "quantised model was not measured.",
            "Relevance labels are a lower bound (mean 1.02 labelled chunks per "
            "question), so absolute recall understates every arm equally; the "
            "delta between arms is the figure this report is for.",
        ],
    }


def _print_table(report: dict) -> None:
    reranked = any("reranked_retrieval" in arm for arm in report["backends"].values())
    header = (
        f"{'arm':<12}{'ms/query':>10}{'p95':>8}{'texts/s':>10}{'MB':>8}"
        f"{'dense r@10':>12}{'Δdense':>9}{'Δserved':>9}{'same lists':>12}"
    )
    print(header)
    print("-" * len(header))
    for name, summary in report["backends"].items():
        delta = summary["retrieval_delta_vs_torch"].get("recall@10", 0.0)
        served = (
            f"{summary['reranked_delta_vs_torch'].get('recall@10', 0.0):>+9.3f}"
            if reranked and "reranked_delta_vs_torch" in summary
            else f"{'—':>9}"
        )
        size = summary["size_bytes"]
        print(
            f"{name:<12}"
            f"{summary['query_latency_ms']['mean']:>10.1f}"
            f"{summary['query_latency_ms']['p95']:>8.1f}"
            f"{summary['passage_throughput']['texts_per_second']:>10.1f}"
            + (f"{size / 1e6:>8.1f}" if size else f"{'—':>8}")
            + f"{summary['retrieval']['recall@10']:>12.3f}"
            f"{delta:>+9.3f}"
            + served
            + f"{summary['identical_result_lists_vs_torch']:>9d}/{report['queries']}"
        )
    print()
    for sentence in report["trade_off"]:
        print(f"  {sentence}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        default="finetuned",
        help="config profile naming the model and index (default: the fine-tuned pair)",
    )
    parser.add_argument("--eval-set", default=DEFAULT_EVAL_SET_PATH)
    parser.add_argument("--split", choices=SPLITS, default=None)
    parser.add_argument("--k", type=int, default=20)
    parser.add_argument(
        "--backends",
        default="torch,torch:cpu,onnx,onnx-int8",
        help=(
            "comma-separated arms to measure. An arm is a backend "
            f"({', '.join(BACKENDS)}), optionally with a torch device pinned as "
            "'torch:cpu' — which is what separates 'ONNX is faster' from 'CPU is "
            "faster at batch 1'."
        ),
    )
    parser.add_argument(
        "--passages", type=int, default=512, help="corpus chunks in the throughput sample"
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument(
        "--no-rerank",
        action="store_true",
        help=(
            "skip the served-path (RRF + cross-encoder) arm. It is the slow half "
            "of this run and the only half that measures what a user would see."
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
    questions = [entry["question"] for entry in entries]
    passages = load_passage_sample("data/chunks", args.passages)
    if not passages:
        raise SystemExit("no corpus chunks under data/chunks — run scripts/run_ingestion.py first")

    arms = [parse_arm(spec) for spec in args.backends.split(",") if spec.strip()]
    if BASELINE_ARM not in [arm.label for arm in arms]:
        raise SystemExit(
            f"the {BASELINE_ARM!r} arm is the baseline every delta is measured "
            "against; a run without it can only report absolute numbers."
        )

    reranker = None
    if not args.no_rerank:
        from duediligence.index.rerank import CrossEncoderReranker

        # Loaded once for every arm: two transformer models resident at a time
        # is already what this machine can carry.
        reranker = CrossEncoderReranker(config.models.reranker_model)

    measurements: dict[str, dict] = {}
    for arm in arms:
        logger.info("measuring arm %s", arm.label)
        measurements[arm.label] = measure_arm(
            arm=arm,
            model_name=model_name,
            questions=questions,
            passages=passages,
            client=client,
            index_name=index_name,
            entries=entries,
            k=args.k,
            batch_size=args.batch_size,
            reranker=reranker,
        )

    export_path = onnx_export_dir(model_name) / "export.json"
    export_report = json.loads(export_path.read_text()) if export_path.is_file() else None

    report = build_report(
        measurements=measurements,
        model_name=model_name,
        profile=args.profile,
        index_name=index_name,
        eval_set_path=args.eval_set,
        split=args.split,
        entries=entries,
        k=args.k,
        export_report=export_report,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n")

    _print_table(report)
    print(f"\nwrote {out_path}")

    url = log_run(
        name=args.run_name,
        config={
            "model": model_name,
            "index": index_name,
            "profile": args.profile,
            "backends": [arm.label for arm in arms],
            "split": report["split"],
            "k": args.k,
        },
        metrics=flatten_metrics(report),
        tags=["onnx", "quantization", "inference"],
        notes="ONNX and INT8 backends against the PyTorch baseline: latency, throughput, recall.",
    )
    if url:
        print(f"tracked: {url}")


if __name__ == "__main__":
    main()
