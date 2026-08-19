"""The fine-tune delta: two retrieval runs, subtracted, with the guards that
make the subtraction mean something.

The bi-encoder was fine-tuned to close a domain gap that BM25 exposed —
dense retrieval scored roughly half of BM25 on every metric — so the value of
that training run is expressed entirely as a *difference* between two
retrieval runs. A difference is the easiest kind of number to get quietly
wrong, in three specific ways this module refuses:

1. **Both arms querying the same index.** Forgetting the profile leaves the
   candidate run reading the baseline index with the baseline model. Nothing
   errors; the delta is exactly zero and looks like an honest null result.
   Two arms on one index raise here instead.
2. **Mixing the reranked and unreranked cells.** The cross-encoder is the
   largest single quality jump in the pipeline, so a bi-encoder gain that
   merely reorders within the pool the reranker is about to reorder anyway is
   invisible in the reranked row, and a gain read off the unreranked row
   overstates what a user of the served system experiences. Both cells are
   reported, and each is labelled with whether the cross-encoder ran.
3. **Scoring on questions that tuning already saw.** The fusion weight of
   0.25 was selected by sweeping against the full eval set, so a delta
   reported there is optimised against twice. The headline is the held-out
   test split; dev and the full set are reported beside it for continuity,
   each labelled with which questions produced it.

BM25 cannot move because the embedding model changed — same text, same
analyzer — so its row across the two arms is a free integrity check, and a
moved one means the arms are not comparable.

Nothing here talks to OpenSearch or loads a model. It reads the report files
``run_retrieval_eval`` already writes, which means the comparison is
recomputable from artifacts long after the machine that produced them is
busy doing something else.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence

from duediligence.eval.eval_set import SPLITS
from duediligence.eval.retrieval_metrics import aggregate_metrics

__all__ = [
    "ALL", "CONFOUNDS", "METRICS", "RERANKED_RETRIEVERS", "UNRERANKED_RETRIEVERS",
    "build_comparison", "compare_groups", "delta_metrics", "reranked_agreement",
    "rows_for_split", "score_rows",
]

#: The metrics the delta is reported on. The retrieval report carries more,
#: but these are the five the published comparison table uses, and a delta
#: is only readable against the table it is a delta from.
METRICS = ("recall@1", "recall@5", "recall@10", "mrr", "ndcg@10")

#: Which run each retriever row is taken from. Reading the unreranked rows
#: off the reranked run would work — they are computed there too — but taking
#: each cell from the run that was configured for it is what makes "four
#: runs, differing only by profile and rerank setting" true of the artifact
#: rather than only of the commands.
UNRERANKED_RETRIEVERS = ("dense", "bm25", "hybrid")
RERANKED_RETRIEVERS = ("hybrid_rerank",)

#: ``rows_for_split``'s name for "do not filter".
ALL = "all"

_K_VALUES = (1, 3, 5, 10, 20)

#: Restated with every delta, because a reader who sees only the difference
#: cannot see what the difference was measured over. Both of these depress
#: the absolute level and neither is fixed by fine-tuning.
CONFOUNDS = (
    "Relevance labels are a floor, not an estimate: they average 1.02 chunks "
    "per question, drawn from a stratified sampled candidate pool rather than "
    "exhaustive judgments over all 38,483 chunks, so a retriever that returns "
    "an unlabelled chunk which does answer the question is scored as missing.",
    "The questions were drafted by reading their labelled chunks, so they "
    "reuse those chunks' vocabulary, which structurally favours lexical "
    "matching over semantic matching. The dense arm of this comparison is "
    "measured under that handicap, and it applies equally to both arms.",
    "The fusion weight of 0.25 used by the hybrid rows was selected by "
    "sweeping against the development split, so hybrid figures on dev carry "
    "that optimisation and the test split does not.",
)


def rows_for_split(report: dict, split: str) -> list[dict]:
    """The per-query rows of one run, restricted to one split.

    ``split="all"`` returns every row — the full-set figures that keep this
    comparable with the published table. Naming a split returns exactly that
    split's rows.

    A row carrying no split raises rather than defaulting, for the same
    reason ``eval_set.load_eval_set`` raises: folding it into dev leaks an
    unexamined question into the tuning set and dropping it silently shrinks
    the eval, and both produce a report that looks clean and is not.
    """
    rows = report["per_query"]
    if split == ALL:
        return list(rows)
    if split not in SPLITS:
        raise ValueError(f"unknown split {split!r}; known: {[*SPLITS, ALL]}")
    unassigned = [row.get("eval_id", "<no eval_id>") for row in rows if not row.get("split")]
    if unassigned:
        raise ValueError(
            f"{len(unassigned)} row(s) in this run carry no split and cannot be "
            f"assigned to one here: {unassigned[:10]}"
            + (" ..." if len(unassigned) > 10 else "")
            + " — re-run the eval against a split-assigned eval set "
            "(scripts/assign_eval_splits.py)"
        )
    return [row for row in rows if row["split"] == split]


def _retrieved(row: dict, retriever: str) -> Sequence[str]:
    key = f"{retriever}_retrieved"
    if key not in row:
        raise KeyError(
            f"run has no {retriever!r} results (missing {key!r} on "
            f"{row.get('eval_id', '<no eval_id>')}) — a reranked row cannot be "
            "read off a --no-rerank run"
        )
    return row[key]


def score_rows(rows: Iterable[dict], retriever: str) -> dict[str, float]:
    """Aggregate metrics for one retriever over one set of per-query rows."""
    pairs = [(_retrieved(row, retriever), set(row["relevant_chunk_ids"])) for row in rows]
    return aggregate_metrics(pairs, k_values=_K_VALUES)


def delta_metrics(
    base: dict[str, float],
    candidate: dict[str, float],
    *,
    metrics: Sequence[str] = METRICS,
) -> dict[str, float]:
    """candidate - base, metric by metric, sign intact.

    Rounded to four places only, which is finer than any difference this eval
    can resolve over 30 questions and coarse enough that float noise does not
    reach a report.
    """
    return {
        metric: round(candidate.get(metric, 0.0) - base.get(metric, 0.0), 4)
        for metric in metrics
        if metric in base or metric in candidate
    }


def _rounded(metrics: dict[str, float], keys: Sequence[str] = METRICS) -> dict[str, float]:
    return {key: round(metrics[key], 4) for key in keys if key in metrics}


def compare_groups(
    base_rows: Iterable[dict],
    candidate_rows: Iterable[dict],
    retriever: str,
    group_key: str,
) -> dict[str, dict]:
    """Base, candidate and delta within each value of ``group_key``.

    Grouping is what separates "the fine-tune helped" from "the fine-tune
    helped on tables" — dense recall on tables was roughly half BM25's, so a
    gain concentrated there is a different finding from a gain spread evenly,
    and a gain concentrated in one category reported as a general improvement
    is the specific overstatement this breakdown exists to prevent.

    Groups are keyed by ``eval_id`` on both sides so a question that appears
    in one run and not the other cannot silently shift a group's membership.
    """
    def grouped(rows: Iterable[dict]) -> dict[str, dict[str, dict]]:
        out: dict[str, dict[str, dict]] = defaultdict(dict)
        for row in rows:
            out[row[group_key]][row["eval_id"]] = row
        return out

    base_groups = grouped(base_rows)
    candidate_groups = grouped(candidate_rows)

    comparison: dict[str, dict] = {}
    for group in sorted(set(base_groups) | set(candidate_groups)):
        shared = sorted(set(base_groups.get(group, {})) & set(candidate_groups.get(group, {})))
        if not shared:
            continue
        base_metrics = score_rows([base_groups[group][i] for i in shared], retriever)
        candidate_metrics = score_rows([candidate_groups[group][i] for i in shared], retriever)
        comparison[group] = {
            "queries": len(shared),
            "base": _rounded(base_metrics),
            "finetuned": _rounded(candidate_metrics),
            "delta": delta_metrics(base_metrics, candidate_metrics),
        }
    return comparison


def reranked_agreement(base_runs: dict[str, dict], finetuned_runs: dict[str, dict]) -> dict:
    """Did the cross-encoder return the *same list*, or merely the same score?

    A null reranked delta has two causes that look identical in a metrics
    table and mean opposite things. Either the reranker took two different
    candidate sets and reordered them into equally good answers — a finding
    about the reranker — or the fine-tuned vectors never reached its input,
    in which case the reranked cell measured nothing about the bi-encoder at
    all and must not be read as evidence that fine-tuning did not help.

    Byte-identical result lists across two arms that provably queried
    different indexes is the signature of the second case, so it is counted
    here rather than inferred from a delta of zero.
    """
    base = {row["eval_id"]: row for row in base_runs["rerank"]["per_query"]}
    candidate = {row["eval_id"]: row for row in finetuned_runs["rerank"]["per_query"]}
    shared = sorted(set(base) & set(candidate))
    identical = sum(
        1 for eval_id in shared
        if list(_retrieved(base[eval_id], "hybrid_rerank"))
        == list(_retrieved(candidate[eval_id], "hybrid_rerank"))
    )
    return {
        "queries": len(shared),
        "identical_reranked_lists": identical,
        "reranked_lists_identical": bool(shared) and identical == len(shared),
    }


def _check_arm_agrees_with_itself(arm: str, runs: dict[str, dict]) -> None:
    """The two runs of one arm differ only by the reranking step.

    dense, BM25 and hybrid are recomputed identically in both, so if they
    disagree the two runs did not see the same index, the same eval set, or
    the same code, and pairing their cells would compare across that
    difference while labelling it as the cross-encoder.
    """
    unreranked = {row["eval_id"]: row for row in runs["no_rerank"]["per_query"]}
    reranked = {row["eval_id"]: row for row in runs["rerank"]["per_query"]}
    shared = set(unreranked) & set(reranked)
    if not shared:
        raise ValueError(
            f"the {arm} arm's two runs share no questions — they were not run "
            "against the same eval set"
        )
    for retriever in UNRERANKED_RETRIEVERS:
        differing = sorted(
            eval_id for eval_id in shared
            if list(_retrieved(unreranked[eval_id], retriever))
            != list(_retrieved(reranked[eval_id], retriever))
        )
        if differing:
            raise ValueError(
                f"the {arm} arm's two runs disagree on {retriever!r} for "
                f"{len(differing)} question(s) ({differing[:5]}) — they differ by "
                "more than the reranking step, so their cells are not comparable"
            )


def _bm25_identical_across_arms(base_runs: dict, finetuned_runs: dict) -> bool:
    base = {row["eval_id"]: list(row["bm25_retrieved"]) for row in base_runs["no_rerank"]["per_query"]}
    candidate = {
        row["eval_id"]: list(row["bm25_retrieved"])
        for row in finetuned_runs["no_rerank"]["per_query"]
    }
    return base == candidate


def _arm_description(runs: dict[str, dict]) -> dict:
    no_rerank, rerank = runs["no_rerank"], runs["rerank"]
    return {
        "index": no_rerank["index"],
        "embedding_model": no_rerank["embedding_model"],
        # The config profile that selected both of the above. ``None`` is the
        # base configuration every other report in this repository used, named
        # as such rather than as a "base" profile so the baseline arm is
        # literally the published configuration and not a re-creation of it.
        "profile": no_rerank.get("profile"),
        "reranker_model": rerank.get("reranker_model"),
        "runs": {
            "no_rerank": {
                "index": no_rerank["index"],
                "embedding_model": no_rerank["embedding_model"],
                "reranker_model": None,
                "report": no_rerank.get("report_path"),
            },
            "rerank": {
                "index": rerank["index"],
                "embedding_model": rerank["embedding_model"],
                "reranker_model": rerank.get("reranker_model"),
                "report": rerank.get("report_path"),
            },
        },
    }


def _training_run(
    training_report: dict | None,
    training_report_path: str | None,
    checkpoint_manifest: dict | None,
) -> dict | None:
    """What produced the weights, and whether that can actually be shown.

    ``transfer_checkpoint.py push`` writes a digest manifest so the weights
    that travel by Hub can be tied back to the run that trained them. Without
    it, the losses in the training report and the vectors in the candidate
    index are two facts with nothing joining them, and a model card that
    cited one against the other would be asserting a link nobody checked.
    That is stated here rather than left for a reader to notice.
    """
    if training_report is None:
        return None
    traceable = bool(checkpoint_manifest and checkpoint_manifest.get("files"))
    note = (
        "The checkpoint's digest manifest (results/training/checkpoint.json) is "
        "present, so these weights are tied to the training run that reported "
        "these losses."
        if traceable else
        "No checkpoint digest manifest (results/training/checkpoint.json) is "
        "present, so the weights that produced the candidate index cannot be "
        "shown to be the ones this training run wrote. The delta below is a "
        "real measurement of the indexed model; attributing it to these "
        "hyperparameters requires running scripts/transfer_checkpoint.py push "
        "on the training machine and committing the manifest."
    )
    return {
        "report": training_report_path,
        "base_model": training_report.get("base_model"),
        "epochs": training_report.get("epochs"),
        "batch_size": training_report.get("batch_size"),
        "learning_rate": training_report.get("learning_rate"),
        "device": training_report.get("device"),
        "train_seconds": training_report.get("train_seconds"),
        "final_train_loss": training_report.get("final_train_loss"),
        "final_eval_loss": training_report.get("final_eval_loss"),
        "weights_traceable_to_this_run": traceable,
        "traceability_note": note,
    }


def _split_comparison(base_runs: dict, finetuned_runs: dict, split: str) -> dict:
    retrievers: dict[str, dict] = {}
    by_chunk_type: dict[str, dict] = {}
    by_question_type: dict[str, dict] = {}

    for run_key, names, reranked in (
        ("no_rerank", UNRERANKED_RETRIEVERS, False),
        ("rerank", RERANKED_RETRIEVERS, True),
    ):
        base_rows = rows_for_split(base_runs[run_key], split)
        candidate_rows = rows_for_split(finetuned_runs[run_key], split)
        for name in names:
            base_metrics = score_rows(base_rows, name)
            candidate_metrics = score_rows(candidate_rows, name)
            retrievers[name] = {
                "cross_encoder": reranked,
                "from_run": run_key,
                "base": _rounded(base_metrics),
                "finetuned": _rounded(candidate_metrics),
                "delta": delta_metrics(base_metrics, candidate_metrics),
            }
            by_chunk_type[name] = compare_groups(base_rows, candidate_rows, name, "chunk_type")
            by_question_type[name] = compare_groups(
                base_rows, candidate_rows, name, "question_type"
            )

    rows = rows_for_split(base_runs["no_rerank"], split)
    return {
        "split": split,
        "queries": len(rows),
        "human_verified_queries": sum(1 for row in rows if row.get("verified")),
        "retrievers": retrievers,
        "by_chunk_type": by_chunk_type,
        "by_question_type": by_question_type,
    }


def build_comparison(
    *,
    base_runs: dict[str, dict],
    finetuned_runs: dict[str, dict],
    training_report: dict | None = None,
    training_report_path: str | None = None,
    checkpoint_manifest: dict | None = None,
    pool_report: dict | None = None,
    headline_split: str = "test",
    splits: Sequence[str] = ("test", "dev", ALL),
) -> dict:
    """The four-run matrix, reduced to the deltas it exists to produce.

    ``base_runs`` and ``finetuned_runs`` each hold the two reports of one arm
    under ``"no_rerank"`` and ``"rerank"``. Together those are the four cells:
    base and fine-tuned, each with and without the cross-encoder.
    """
    if base_runs["no_rerank"]["index"] == finetuned_runs["no_rerank"]["index"]:
        raise ValueError(
            "both arms scored the same index "
            f"({base_runs['no_rerank']['index']!r}) — the candidate run needs "
            "DUEDILIGENCE_CONFIG_PROFILE=finetuned. A delta measured this way "
            "is exactly zero for a reason that has nothing to do with the model."
        )
    _check_arm_agrees_with_itself("base", base_runs)
    _check_arm_agrees_with_itself("finetuned", finetuned_runs)

    by_split = {
        split: _split_comparison(base_runs, finetuned_runs, split) for split in splits
    }
    headline = by_split[headline_split]

    return {
        "comparison": "fine-tuned bi-encoder vs off-the-shelf bge-small-en-v1.5",
        "eval_set": base_runs["no_rerank"]["eval_set"],
        "headline_split": headline_split,
        "headline_split_rationale": (
            "The fusion weight and the rerank depth were both selected by "
            "sweeping against the development split, so the test split is the "
            "only one no tuning decision has touched. Full-set figures are "
            "reported beside it for continuity with the published table, not "
            "as the headline."
        ),
        "arms": {
            "base": _arm_description(base_runs),
            "finetuned": _arm_description(finetuned_runs),
        },
        "consistency": {
            "arms_use_different_indexes": True,
            "each_arm_agrees_with_itself": True,
            "bm25_identical_across_arms": _bm25_identical_across_arms(
                base_runs, finetuned_runs
            ),
            "bm25_check_note": (
                "BM25 reads the same text through the same analyzer in both "
                "indexes, so it cannot move because the embedding model "
                "changed. A False here means the two arms are not comparable."
            ),
        },
        "rerank_absorption": {
            **reranked_agreement(base_runs, finetuned_runs),
            "note": (
                "The cross-encoder reranks a fused candidate pool. If the two "
                "arms hand it the same candidate documents, it returns the same "
                "list and the reranked delta is zero by construction rather than "
                "by measurement — the fine-tuned vectors changed the order of "
                "the pool, not its membership, and the cross-encoder discards "
                "that order. Identical result lists across two arms that "
                "provably queried different indexes are the signature of "
                "exactly that, and mean the reranked cell says nothing about "
                "the bi-encoder."
            ),
            "candidate_pool": pool_report,
        },
        "training_run": _training_run(
            training_report, training_report_path, checkpoint_manifest
        ),
        "confounds": list(CONFOUNDS),
        "headline": headline,
        "splits": by_split,
    }
