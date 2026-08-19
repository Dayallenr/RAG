"""The fine-tune delta comparison.

The number this whole training path exists for is a *difference* between two
retrieval runs, and a difference is the easiest kind of number to get quietly
wrong: score two runs that used the same index and the delta is zero for a
reason that has nothing to do with the model; take the reranked row from one
arm and the unreranked row from the other and the delta is whatever the
mismatch happens to produce. These tests pin the arithmetic and the guards.
"""
from __future__ import annotations

import pytest

from duediligence.eval.finetune_delta import (
    METRICS,
    build_comparison,
    compare_groups,
    delta_metrics,
    rows_for_split,
    score_rows,
)


def _row(eval_id, split, *, chunk_type="paragraph", question_type="narrative",
         relevant=("gold",), dense=("gold",), bm25=("gold",), hybrid=("gold",),
         rerank=None, verified=True):
    row = {
        "eval_id": eval_id,
        "split": split,
        "chunk_type": chunk_type,
        "question_type": question_type,
        "relevant_chunk_ids": list(relevant),
        "verified": verified,
        "dense_retrieved": list(dense),
        "bm25_retrieved": list(bm25),
        "hybrid_retrieved": list(hybrid),
    }
    if rerank is not None:
        row["hybrid_rerank_retrieved"] = list(rerank)
    return row


def _report(rows, *, index="duediligence-chunks", model="BAAI/bge-small-en-v1.5",
            reranker=None):
    return {
        "eval_set": "data/eval_set.jsonl",
        "split": "all",
        "index": index,
        "embedding_model": model,
        "reranker_model": reranker,
        "k": 20,
        "candidate_k": 50,
        "per_query": rows,
    }


def _arm(*, index, model, dense_hit_at, rerank_hit_at=1):
    """One profile's pair of runs, with the gold chunk placed at a chosen rank."""
    def ranked(position):
        listed = [f"noise{i}" for i in range(5)]
        listed[position - 1] = "gold"
        return listed

    unreranked = [
        _row("q1", "test", dense=ranked(dense_hit_at)),
        _row("q2", "dev", dense=ranked(dense_hit_at), chunk_type="table",
             question_type="table"),
    ]
    reranked = [
        dict(row, hybrid_rerank_retrieved=ranked(rerank_hit_at)) for row in unreranked
    ]
    return {
        "no_rerank": _report(unreranked, index=index, model=model),
        "rerank": _report(
            reranked, index=index, model=model,
            reranker="cross-encoder/ms-marco-MiniLM-L-6-v2",
        ),
    }


class TestRowsForSplit:
    def test_selects_only_that_splits_rows(self):
        report = _report([_row("q1", "test"), _row("q2", "dev")])
        assert [r["eval_id"] for r in rows_for_split(report, "test")] == ["q1"]

    def test_all_returns_every_row(self):
        report = _report([_row("q1", "test"), _row("q2", "dev")])
        assert len(rows_for_split(report, "all")) == 2

    def test_a_row_with_no_split_is_an_error_rather_than_a_guess(self):
        # Folding it into dev leaks a question into tuning; dropping it
        # shrinks the eval silently. Both look clean and are not.
        report = _report([dict(_row("q1", "test"), split=None)])
        with pytest.raises(ValueError, match="split"):
            rows_for_split(report, "test")

    def test_an_unknown_split_is_rejected(self):
        with pytest.raises(ValueError, match="unknown split"):
            rows_for_split(_report([_row("q1", "test")]), "holdout")


class TestScoring:
    def test_scores_the_named_retrievers_own_result_list(self):
        rows = [_row("q1", "test", dense=["gold"], bm25=["miss", "gold"])]
        assert score_rows(rows, "dense")["recall@1"] == 1.0
        assert score_rows(rows, "bm25")["recall@1"] == 0.0

    def test_a_retriever_absent_from_the_run_is_named_in_the_error(self):
        with pytest.raises(KeyError, match="hybrid_rerank"):
            score_rows([_row("q1", "test")], "hybrid_rerank")

    def test_delta_is_a_plain_subtraction_and_keeps_its_sign(self):
        base = {"recall@10": 0.700, "mrr": 0.400}
        candidate = {"recall@10": 0.600, "mrr": 0.450}
        deltas = delta_metrics(base, candidate, metrics=("recall@10", "mrr"))
        assert deltas["recall@10"] == pytest.approx(-0.1)
        assert deltas["mrr"] == pytest.approx(0.05)

    def test_groups_are_compared_within_the_same_group(self):
        base = [_row("q1", "test", chunk_type="table", dense=["miss", "gold"])]
        candidate = [_row("q1", "test", chunk_type="table", dense=["gold"])]
        groups = compare_groups(base, candidate, "dense", "chunk_type")
        assert groups["table"]["delta"]["recall@1"] == pytest.approx(1.0)
        assert groups["table"]["base"]["recall@1"] == 0.0


class TestBuildComparison:
    def _runs(self, *, finetuned_dense_rank=1, finetuned_index="duediligence-chunks-finetuned"):
        base = _arm(index="duediligence-chunks", model="BAAI/bge-small-en-v1.5",
                    dense_hit_at=3)
        finetuned = _arm(index=finetuned_index, model="models/bge-small-duediligence",
                         dense_hit_at=finetuned_dense_rank)
        return base, finetuned

    def test_reports_a_positive_delta_where_the_fine_tune_helped(self):
        base, finetuned = self._runs(finetuned_dense_rank=1)
        report = build_comparison(base_runs=base, finetuned_runs=finetuned)
        dense = report["splits"]["test"]["retrievers"]["dense"]
        assert dense["delta"]["recall@1"] == pytest.approx(1.0)

    def test_reports_a_negative_delta_exactly_as_plainly(self):
        base, finetuned = self._runs(finetuned_dense_rank=5)
        report = build_comparison(base_runs=base, finetuned_runs=finetuned)
        dense = report["splits"]["test"]["retrievers"]["dense"]
        assert dense["delta"]["recall@1"] == 0.0
        assert dense["delta"]["recall@10"] == 0.0
        assert dense["delta"]["mrr"] < 0

    def test_the_unreranked_rows_come_from_the_unreranked_run(self):
        base, finetuned = self._runs()
        report = build_comparison(base_runs=base, finetuned_runs=finetuned)
        for name in ("dense", "bm25", "hybrid"):
            assert report["splits"]["test"]["retrievers"][name]["cross_encoder"] is False
        assert report["splits"]["test"]["retrievers"]["hybrid_rerank"]["cross_encoder"] is True

    def test_every_metric_the_ticket_asks_for_is_present(self):
        base, finetuned = self._runs()
        report = build_comparison(base_runs=base, finetuned_runs=finetuned)
        deltas = report["splits"]["test"]["retrievers"]["hybrid"]["delta"]
        assert set(METRICS) <= set(deltas)

    def test_the_headline_split_is_the_held_out_one(self):
        base, finetuned = self._runs()
        report = build_comparison(base_runs=base, finetuned_runs=finetuned)
        assert report["headline_split"] == "test"
        assert report["headline"]["split"] == "test"
        # dev and the full set stay available for continuity, labelled.
        assert set(report["splits"]) == {"test", "dev", "all"}

    def test_each_arm_records_the_model_and_index_that_produced_it(self):
        base, finetuned = self._runs()
        report = build_comparison(base_runs=base, finetuned_runs=finetuned)
        assert report["arms"]["finetuned"]["index"] == "duediligence-chunks-finetuned"
        assert report["arms"]["finetuned"]["embedding_model"] == "models/bge-small-duediligence"
        assert report["arms"]["base"]["index"] == "duediligence-chunks"

    def test_two_arms_on_one_index_is_refused(self):
        # The single most likely way to produce a meaningless zero delta is
        # to forget the profile, which leaves both arms querying the baseline
        # index with the baseline model.
        base, finetuned = self._runs(finetuned_index="duediligence-chunks")
        with pytest.raises(ValueError, match="same index"):
            build_comparison(base_runs=base, finetuned_runs=finetuned)

    def test_the_two_runs_of_one_arm_must_agree_on_their_shared_rows(self):
        base, finetuned = self._runs()
        drifted = dict(base["rerank"])
        drifted["per_query"] = [
            dict(row, bm25_retrieved=["something", "else"]) for row in drifted["per_query"]
        ]
        with pytest.raises(ValueError, match="disagree"):
            build_comparison(base_runs={"no_rerank": base["no_rerank"], "rerank": drifted},
                             finetuned_runs=finetuned)

    def test_bm25_is_checked_for_being_unchanged_across_arms(self):
        # Same text, same analyzer: BM25 cannot move because the embedding
        # model changed, so a moved BM25 row means the two arms are not
        # comparable.
        base, finetuned = self._runs()
        report = build_comparison(base_runs=base, finetuned_runs=finetuned)
        assert report["consistency"]["bm25_identical_across_arms"] is True

    def test_deltas_are_broken_down_by_chunk_and_question_type(self):
        base, finetuned = self._runs()
        report = build_comparison(base_runs=base, finetuned_runs=finetuned)
        full = report["splits"]["all"]
        assert "table" in full["by_chunk_type"]["dense"]
        assert "narrative" in full["by_question_type"]["dense"]

    def test_the_human_verified_count_travels_with_every_split(self):
        base, finetuned = self._runs()
        report = build_comparison(base_runs=base, finetuned_runs=finetuned)
        assert report["splits"]["test"]["queries"] == 1
        assert report["splits"]["test"]["human_verified_queries"] == 1

    def test_the_known_confounds_are_restated_with_the_delta(self):
        base, finetuned = self._runs()
        report = build_comparison(base_runs=base, finetuned_runs=finetuned)
        confounds = " ".join(report["confounds"]).lower()
        assert "1.02" in confounds
        assert "lexical" in confounds

    def test_the_training_run_is_linked_to_the_evaluation_that_scored_it(self):
        base, finetuned = self._runs()
        training = {
            "base_model": "BAAI/bge-small-en-v1.5",
            "epochs": 1.0,
            "batch_size": 32,
            "final_eval_loss": 0.52,
            "device": "cuda",
        }
        report = build_comparison(base_runs=base, finetuned_runs=finetuned,
                                  training_report=training,
                                  training_report_path="results/training/report.json")
        assert report["training_run"]["report"] == "results/training/report.json"
        assert report["training_run"]["final_eval_loss"] == 0.52
        assert report["training_run"]["batch_size"] == 32

    def test_an_unlinkable_checkpoint_is_stated_not_assumed(self):
        base, finetuned = self._runs()
        report = build_comparison(base_runs=base, finetuned_runs=finetuned,
                                  training_report={"epochs": 1.0},
                                  checkpoint_manifest=None)
        traceability = report["training_run"]["weights_traceable_to_this_run"]
        assert traceability is False
        assert "manifest" in report["training_run"]["traceability_note"].lower()

    def test_a_manifest_that_matches_the_weights_ties_them_to_the_run(self):
        base, finetuned = self._runs()
        report = build_comparison(
            base_runs=base, finetuned_runs=finetuned, training_report={"epochs": 1.0},
            checkpoint_manifest={"files": {"model.safetensors": "abc123"}},
            checkpoint_problems=[],
        )
        assert report["training_run"]["weights_traceable_to_this_run"] is True

    def test_a_manifest_that_does_not_match_the_weights_certifies_nothing(self):
        """The one way this check could certify something false.

        A manifest is a claim about specific bytes. Treating its mere presence
        as proof means a checkpoint that arrived corrupted, or a different
        checkpoint entirely, reads as tied to the run — which is worse than
        reporting no manifest at all, because it looks checked.
        """
        base, finetuned = self._runs()
        report = build_comparison(
            base_runs=base, finetuned_runs=finetuned, training_report={"epochs": 1.0},
            checkpoint_manifest={"files": {"model.safetensors": "abc123"}},
            checkpoint_problems=["digest mismatch: modules.json (expected 5861…, got a0f5…)"],
        )
        training = report["training_run"]
        assert training["weights_traceable_to_this_run"] is False
        assert "modules.json" in training["traceability_note"], (
            "the note must name what failed, or nobody can tell a corrupted "
            "weight file from a rewritten metadata file"
        )

    def test_an_unverified_manifest_is_not_a_verified_one(self):
        """Manifest present, digests never compared: still not a tie."""
        base, finetuned = self._runs()
        report = build_comparison(
            base_runs=base, finetuned_runs=finetuned, training_report={"epochs": 1.0},
            checkpoint_manifest={"files": {"model.safetensors": "abc123"}},
            checkpoint_problems=None,
        )
        assert report["training_run"]["weights_traceable_to_this_run"] is False


class TestRerankAbsorption:
    """A zero delta after reranking has two very different causes.

    Either the cross-encoder reordered two different candidate sets into the
    same answer — a genuine finding about the reranker — or the fine-tuned
    vectors never reached the reranker's input at all, in which case the
    reranked cell measured nothing about the bi-encoder. The reranked lists
    being *identical* rather than merely equal-scoring is what separates the
    two, so it is computed rather than left to a reader's assumption.
    """

    def test_counts_the_queries_whose_reranked_lists_are_identical(self):
        from duediligence.eval.finetune_delta import reranked_agreement

        base = _arm(index="a", model="m1", dense_hit_at=3)
        finetuned = _arm(index="b", model="m2", dense_hit_at=1)
        agreement = reranked_agreement(base, finetuned)
        # Both arms place the reranked gold chunk at rank 1 by construction.
        assert agreement["queries"] == 2
        assert agreement["identical_reranked_lists"] == 2
        assert agreement["reranked_lists_identical"] is True

    def test_a_differing_reranked_list_is_reported_as_such(self):
        from duediligence.eval.finetune_delta import reranked_agreement

        base = _arm(index="a", model="m1", dense_hit_at=3)
        finetuned = _arm(index="b", model="m2", dense_hit_at=1, rerank_hit_at=4)
        agreement = reranked_agreement(base, finetuned)
        assert agreement["identical_reranked_lists"] == 0
        assert agreement["reranked_lists_identical"] is False

    def test_the_comparison_carries_it_beside_the_reranked_delta(self):
        base = _arm(index="a", model="m1", dense_hit_at=3)
        finetuned = _arm(index="b", model="m2", dense_hit_at=1)
        report = build_comparison(base_runs=base, finetuned_runs=finetuned)
        assert report["rerank_absorption"]["reranked_lists_identical"] is True
        assert "candidate" in report["rerank_absorption"]["note"].lower()

    def test_a_pool_report_is_folded_in_when_one_was_produced(self):
        base = _arm(index="a", model="m1", dense_hit_at=3)
        finetuned = _arm(index="b", model="m2", dense_hit_at=1)
        pool = {"pool_equals_bm25_candidates": 30, "queries": 30}
        report = build_comparison(base_runs=base, finetuned_runs=finetuned,
                                  pool_report=pool)
        assert report["rerank_absorption"]["candidate_pool"] == pool

    def test_no_pool_report_is_recorded_as_absent_not_as_a_finding(self):
        base = _arm(index="a", model="m1", dense_hit_at=3)
        finetuned = _arm(index="b", model="m2", dense_hit_at=1)
        report = build_comparison(base_runs=base, finetuned_runs=finetuned)
        assert report["rerank_absorption"]["candidate_pool"] is None


class TestDenseOnlyEntryDepth:
    """The arithmetic behind the null reranked delta.

    RRF scores a document ``weight / (rrf_k + rank)``. A document only dense
    retrieval found scores at best ``dense_weight / (rrf_k + 1)``, and it
    enters the fused pool only by beating BM25's document at the pool's last
    position. Below that depth the pool's membership belongs to BM25 alone,
    whatever the embedding model does — which is why the reranked cell of the
    matrix cannot see a bi-encoder change.
    """

    def test_the_shipped_configuration_admits_no_dense_only_document_at_depth_50(self):
        from scripts.verify_rerank_pool import dense_only_depth_threshold

        # 0.25/(60+1) beats 1/(60+c) only once c > 184.
        assert dense_only_depth_threshold(0.25) == 184

    def test_equal_weighting_admits_them_immediately(self):
        from scripts.verify_rerank_pool import dense_only_depth_threshold

        assert dense_only_depth_threshold(1.0) == 1

    def test_a_zero_weighted_retriever_never_contributes(self):
        from scripts.verify_rerank_pool import dense_only_depth_threshold

        assert dense_only_depth_threshold(0.0) == 0


class TestArmsNameTheirProfile:
    def test_the_candidate_arm_records_the_profile_that_selected_it(self):
        base = _arm(index="a", model="m1", dense_hit_at=3)
        finetuned = _arm(index="b", model="m2", dense_hit_at=1)
        for run in finetuned.values():
            run["profile"] = "finetuned"
        report = build_comparison(base_runs=base, finetuned_runs=finetuned)
        assert report["arms"]["finetuned"]["profile"] == "finetuned"

    def test_the_baseline_arm_records_no_profile_rather_than_inventing_one(self):
        # The baseline is the base configuration, not a "base" profile — the
        # published table was produced without one.
        base = _arm(index="a", model="m1", dense_hit_at=3)
        finetuned = _arm(index="b", model="m2", dense_hit_at=1)
        report = build_comparison(base_runs=base, finetuned_runs=finetuned)
        assert report["arms"]["base"]["profile"] is None


class TestArmsMustScoreTheSameQuestions:
    """A split label can move between two runs, and nothing else would notice.

    ``scripts/assign_eval_splits.py`` leaves existing rows alone, but reports
    of different vintage combined with ``--from-reports`` can still disagree
    about which questions are held out. Both arms would then cover all 101
    questions, BM25 would still match across arms, and the test-split delta
    would compare one arm's 30 questions against a different 30 — a clean
    report over two populations.
    """

    def _arms_disagreeing_on_split(self):
        base = _arm(index="a", model="m1", dense_hit_at=3)
        finetuned = _arm(index="b", model="m2", dense_hit_at=1)
        for run in finetuned.values():
            run["per_query"] = [
                dict(row, split="dev" if row["split"] == "test" else "test")
                for row in run["per_query"]
            ]
        return base, finetuned

    def test_a_split_that_moved_between_runs_is_refused(self):
        base, finetuned = self._arms_disagreeing_on_split()
        with pytest.raises(ValueError, match="different questions"):
            build_comparison(base_runs=base, finetuned_runs=finetuned)

    def test_the_message_names_the_split_that_disagrees(self):
        base, finetuned = self._arms_disagreeing_on_split()
        with pytest.raises(ValueError, match="test"):
            build_comparison(base_runs=base, finetuned_runs=finetuned)

    def test_matching_splits_are_accepted(self):
        base = _arm(index="a", model="m1", dense_hit_at=3)
        finetuned = _arm(index="b", model="m2", dense_hit_at=1)
        report = build_comparison(base_runs=base, finetuned_runs=finetuned)
        assert report["splits"]["test"]["queries"] == 1
