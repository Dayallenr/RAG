"""Tests for retrieval metrics — hand-computed expected values, not
snapshots of what the code currently returns."""
from __future__ import annotations

import math

import pytest

from duediligence.eval.retrieval_metrics import (
    aggregate_metrics,
    average_precision,
    hit_rate_at_k,
    ndcg_at_k,
    recall_at_k,
    reciprocal_rank,
)


class TestRecallAtK:
    def test_counts_only_relevant_within_k(self):
        retrieved = ["a", "b", "c", "d"]
        # 2 of the 3 relevant ids are in the top 3.
        assert recall_at_k(retrieved, {"a", "c", "z"}, 3) == pytest.approx(2 / 3)

    def test_result_beyond_k_does_not_count(self):
        assert recall_at_k(["x", "y", "a"], {"a"}, 2) == 0.0
        assert recall_at_k(["x", "y", "a"], {"a"}, 3) == 1.0

    def test_empty_ground_truth_is_zero_not_a_crash(self):
        assert recall_at_k(["a"], set(), 5) == 0.0

    def test_duplicate_relevant_ids_in_ground_truth_do_not_inflate(self):
        # Ground truth is a set — a repeated id must not make the
        # denominator larger than the number of distinct relevant chunks.
        assert recall_at_k(["a"], ["a", "a"], 5) == 1.0


class TestHitRateAtK:
    def test_one_hit_is_enough(self):
        assert hit_rate_at_k(["x", "a", "y"], {"a", "b", "c"}, 3) == 1.0

    def test_no_hit_in_window(self):
        assert hit_rate_at_k(["x", "y", "a"], {"a"}, 2) == 0.0


class TestReciprocalRank:
    def test_uses_first_relevant_rank(self):
        assert reciprocal_rank(["x", "y", "a", "b"], {"a", "b"}) == pytest.approx(1 / 3)

    def test_first_position_is_one(self):
        assert reciprocal_rank(["a"], {"a"}) == 1.0

    def test_no_relevant_result_scores_zero(self):
        assert reciprocal_rank(["x", "y"], {"a"}) == 0.0


class TestNdcgAtK:
    def test_perfect_ranking_is_one(self):
        assert ndcg_at_k(["a", "b", "c"], {"a", "b", "c"}, 3) == pytest.approx(1.0)

    def test_reversed_ranking_scores_below_perfect(self):
        good = ndcg_at_k(["a", "b", "x", "y"], {"a", "b"}, 4)
        bad = ndcg_at_k(["x", "y", "a", "b"], {"a", "b"}, 4)
        assert good == pytest.approx(1.0)
        assert 0.0 < bad < good

    def test_matches_hand_computed_value(self):
        # One relevant chunk at rank 2: DCG = 1/log2(3); ideal (one relevant
        # chunk, so ideal puts it at rank 1) = 1/log2(2) = 1.
        expected = (1 / math.log2(3)) / 1.0
        assert ndcg_at_k(["x", "a", "y"], {"a"}, 3) == pytest.approx(expected)

    def test_more_relevant_than_k_can_still_reach_one(self):
        # 5 relevant chunks but k=2: the ideal DCG is computed over the 2
        # reachable positions, so a ranking that fills both scores 1.0
        # rather than being capped below it by an impossible ideal.
        assert ndcg_at_k(["a", "b", "c"], {"a", "b", "c", "d", "e"}, 2) == pytest.approx(1.0)


class TestAveragePrecision:
    def test_matches_hand_computed_value(self):
        # Relevant at ranks 1 and 3: (1/1 + 2/3) / 2.
        expected = (1.0 + 2 / 3) / 2
        assert average_precision(["a", "x", "b", "y"], {"a", "b"}) == pytest.approx(expected)

    def test_missing_relevant_chunk_costs_score(self):
        # Only one of two relevant chunks retrieved, at rank 1: (1/1) / 2.
        assert average_precision(["a", "x", "y"], {"a", "b"}) == pytest.approx(0.5)


class TestAggregateMetrics:
    def test_averages_across_queries(self):
        per_query = [
            (["a", "x", "y"], {"a"}),  # perfect
            (["x", "y", "z"], {"b"}),  # complete miss
        ]
        metrics = aggregate_metrics(per_query, k_values=(1, 3))

        assert metrics["queries"] == 2
        assert metrics["recall@3"] == pytest.approx(0.5)
        assert metrics["hit_rate@1"] == pytest.approx(0.5)
        # A failed query contributes 0 rather than being dropped.
        assert metrics["mrr"] == pytest.approx(0.5)

    def test_queries_without_ground_truth_are_skipped(self):
        per_query = [(["a"], {"a"}), (["b"], set())]
        metrics = aggregate_metrics(per_query, k_values=(1,))
        assert metrics["queries"] == 1
        assert metrics["recall@1"] == pytest.approx(1.0)

    def test_all_empty_ground_truth_returns_empty(self):
        assert aggregate_metrics([(["a"], set())]) == {}
