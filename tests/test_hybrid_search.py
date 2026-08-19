"""Tests for Reciprocal Rank Fusion and the hybrid search wiring."""
from __future__ import annotations

import pytest

from duediligence.index.hybrid_search import (
    DEFAULT_RRF_K,
    hybrid_search,
    reciprocal_rank_fusion,
)


class TestReciprocalRankFusion:
    def test_matches_hand_computed_scores(self):
        # "a" is rank 1 for one retriever and rank 2 for the other.
        fused = dict(reciprocal_rank_fusion([["a", "b"], ["b", "a"]], k=60))
        assert fused["a"] == pytest.approx(1 / 61 + 1 / 62)
        assert fused["b"] == pytest.approx(1 / 62 + 1 / 61)

    def test_document_found_by_both_beats_one_found_by_either_alone(self):
        # This is the whole point of fusion: agreement across retrievers with
        # different failure modes is evidence.
        ranked = reciprocal_rank_fusion([["x", "a"], ["y", "a"]])
        assert ranked[0][0] == "a"

    def test_a_single_top_hit_does_not_automatically_dominate(self):
        # "solo" is rank 1 for one retriever only; "both" is rank 2 for both.
        # With k=60 the damping means agreement wins.
        ranked = dict(reciprocal_rank_fusion([["solo", "both"], ["other", "both"]]))
        assert ranked["both"] > ranked["solo"]

    def test_k_controls_how_much_agreement_outweighs_a_single_top_hit(self):
        # A single rank-1 hit can never beat two rank-2 hits under RRF —
        # 1/(k+1) > 2/(k+2) has no solution for k >= 0 — but k does control
        # the size of the gap, which is the tunable this parameter buys.
        def gap(k):
            scores = dict(reciprocal_rank_fusion([["solo", "both"], ["other", "both"]], k=k))
            return scores["both"] / scores["solo"]

        assert gap(1) < gap(60)
        assert gap(1) > 1.0  # agreement still wins, just by less

    def test_weights_scale_each_retriever(self):
        unweighted = dict(reciprocal_rank_fusion([["a"], ["b"]]))
        weighted = dict(reciprocal_rank_fusion([["a"], ["b"]], weights=[3.0, 1.0]))
        assert unweighted["a"] == pytest.approx(unweighted["b"])
        assert weighted["a"] == pytest.approx(3 * weighted["b"])

    def test_mismatched_weights_are_rejected(self):
        with pytest.raises(ValueError, match="2 rankings but 3 weights"):
            reciprocal_rank_fusion([["a"], ["b"]], weights=[1.0, 1.0, 1.0])

    def test_ties_break_deterministically_on_chunk_id(self):
        # Identical rankings give every doc the same score; the order must
        # still be stable across runs or the eval is not reproducible.
        first = reciprocal_rank_fusion([["b", "a"], ["a", "b"]])
        second = reciprocal_rank_fusion([["a", "b"], ["b", "a"]])
        assert [c for c, _ in first] == [c for c, _ in second] == ["a", "b"]

    def test_empty_rankings_produce_no_results(self):
        assert reciprocal_rank_fusion([[], []]) == []

    def test_default_k_is_the_published_value(self):
        assert DEFAULT_RRF_K == 60


class FusionStubClient:
    """Returns a fixed lexical/dense split so fusion can be checked end to end."""

    def __init__(self):
        self.calls = []

    def search(self, *, index, body):
        self.calls.append(body)
        if "knn" in body["query"]:
            ids = ["dense1", "shared", "dense2"]
        else:
            ids = ["lex1", "shared", "lex2"]
        return {
            "hits": {
                "hits": [
                    {"_id": i, "_score": 1.0, "_source": {"text": i, "chunk_type": "paragraph"}}
                    for i in ids
                ]
            }
        }


class TestHybridSearch:
    def test_document_returned_by_both_retrievers_ranks_first(self):
        results = hybrid_search(FusionStubClient(), "idx", "q", [0.1] * 384, k=3)
        assert results[0]["chunk_id"] == "shared"

    def test_returns_at_most_k_hits(self):
        results = hybrid_search(FusionStubClient(), "idx", "q", [0.1] * 384, k=2)
        assert len(results) == 2

    def test_hits_carry_fused_score_and_metadata(self):
        results = hybrid_search(FusionStubClient(), "idx", "q", [0.1] * 384, k=1)
        hit = results[0]
        # Score is the RRF score, not either retriever's raw score. "shared"
        # is rank 2 in both rankings, and dense contributes at 0.25 weight.
        assert hit["score"] == pytest.approx(1 / 62 + 0.25 / 62)
        assert hit["chunk_type"] == "paragraph"

    def test_asks_each_retriever_for_the_full_candidate_pool(self):
        client = FusionStubClient()
        hybrid_search(client, "idx", "q", [0.1] * 384, k=5, candidate_k=40)
        # Fusion can only consider what a retriever returned, so candidate
        # depth must not collapse to k.
        assert all(body["size"] == 40 for body in client.calls)

    def test_ef_search_reaches_the_dense_half_and_only_the_dense_half(self):
        # ef_search is an HNSW search-time parameter with no lexical
        # counterpart; putting it on the BM25 query would be rejected by
        # OpenSearch, and dropping it silently would make the sweep's
        # through-the-pipeline arm measure the default it meant to change.
        client = FusionStubClient()
        hybrid_search(client, "idx", "q", [0.1] * 384, k=5, candidate_k=40, ef_search=200)
        dense = [b for b in client.calls if "knn" in b["query"]]
        lexical = [b for b in client.calls if "knn" not in b["query"]]
        assert dense[0]["query"]["knn"]["embedding"]["method_parameters"] == {"ef_search": 200}
        assert all("method_parameters" not in str(b) for b in lexical)

    def test_no_ef_search_leaves_the_dense_query_at_the_engine_default(self):
        client = FusionStubClient()
        hybrid_search(client, "idx", "q", [0.1] * 384, k=5, candidate_k=40)
        dense = [b for b in client.calls if "knn" in b["query"]]
        assert "method_parameters" not in dense[0]["query"]["knn"]["embedding"]


class TestTunedDefaults:
    def test_dense_defaults_to_quarter_weight_not_equal(self):
        from duediligence.index.hybrid_search import DEFAULT_DENSE_WEIGHT

        # Equal weighting measured *worse* than BM25 alone on this corpus
        # (ablation A); the default must not silently be 1.0.
        assert DEFAULT_DENSE_WEIGHT == 0.25

    def test_hybrid_search_applies_the_tuned_weight_by_default(self):
        client = FusionStubClient()
        # k=5 so every document is present; at the tuned weight the two
        # dense-only hits fall out of the top 3 entirely, which is the
        # behaviour being asserted.
        results = hybrid_search(client, "idx", "q", [0.1] * 384, k=5)
        scores = {h["chunk_id"]: h["score"] for h in results}
        # lex1 is lexical rank 1; dense1 is dense rank 1 at 0.25 weight.
        assert scores["lex1"] > scores["dense1"]
        assert scores["dense1"] == pytest.approx(0.25 / 61)

    def test_explicit_weights_still_override_the_default(self):
        client = FusionStubClient()
        results = hybrid_search(client, "idx", "q", [0.1] * 384, k=5, weights=[1.0, 1.0])
        scores = {h["chunk_id"]: h["score"] for h in results}
        assert scores["lex1"] == pytest.approx(scores["dense1"])
