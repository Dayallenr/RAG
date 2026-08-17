"""Tests for hard-negative mining and the training split."""
from __future__ import annotations

from duediligence.train.mine import (
    normalize_company_names,
    select_negatives,
    split_by_query,
)


class TestNormalizeCompanyNames:
    def test_replaces_title_cased_ticker(self):
        # The actual artifact in the generated data.
        assert normalize_company_names("What is Colb's dividend policy?") == (
            "What is Columbia Banking System's dividend policy?"
        )

    def test_replaces_uppercase_ticker(self):
        assert "WesBanco" in normalize_company_names("What did WSBC report?")

    def test_leaves_real_names_alone(self):
        question = "What was Columbia Banking System's net income?"
        assert normalize_company_names(question) == question

    def test_does_not_match_inside_a_longer_word(self):
        # "Colbert" must not become "Columbia Banking Systemert".
        assert normalize_company_names("Who is Colbert?") == "Who is Colbert?"

    def test_handles_several_tickers_in_one_query(self):
        out = normalize_company_names("Did Colb acquire Umpq?")
        assert "Columbia Banking System" in out and "Umpqua Holdings" in out

    def test_a_query_with_no_ticker_is_unchanged(self):
        assert normalize_company_names("What were the merger terms?") == (
            "What were the merger terms?"
        )


class TestSelectNegatives:
    def test_excludes_the_positive(self):
        # Training the model to push away a passage that answers the query
        # would be actively harmful.
        assert "p" not in select_negatives(["a", "p", "b", "c"], "p", n=3)

    def test_returns_the_requested_count(self):
        assert len(select_negatives(["a", "b", "c", "d", "e"], "p", n=3)) == 3

    def test_preserves_retrieval_order(self):
        assert select_negatives(["a", "b", "c"], "p", n=2) == ["a", "b"]

    def test_skip_top_drops_the_hardest_hits(self):
        # The top non-positive hit is sometimes a genuine near-duplicate —
        # the same event reported in both companies' filings.
        assert select_negatives(["a", "b", "c", "d"], "p", n=2, skip_top=1) == ["b", "c"]

    def test_handles_fewer_candidates_than_requested(self):
        assert select_negatives(["a"], "p", n=5) == ["a"]

    def test_handles_a_result_list_of_only_the_positive(self):
        assert select_negatives(["p"], "p", n=3) == []


class TestSplitByQuery:
    def _rows(self, n_queries=20, per_query=3):
        return [
            {"query": f"question {q}", "positive": f"p{q}", "negative": f"n{q}-{i}"}
            for q in range(n_queries)
            for i in range(per_query)
        ]

    def test_no_query_appears_on_both_sides(self):
        train, validation = split_by_query(self._rows())
        assert not ({r["query"] for r in train} & {r["query"] for r in validation})

    def test_every_row_lands_somewhere(self):
        rows = self._rows()
        train, validation = split_by_query(rows)
        assert len(train) + len(validation) == len(rows)

    def test_all_triplets_of_a_query_stay_together(self):
        rows = self._rows(n_queries=10, per_query=3)
        train, validation = split_by_query(rows)
        for split in (train, validation):
            counts: dict[str, int] = {}
            for row in split:
                counts[row["query"]] = counts.get(row["query"], 0) + 1
            assert all(c == 3 for c in counts.values())

    def test_the_split_is_reproducible(self):
        rows = self._rows()
        first = split_by_query(rows, seed=17)[1]
        second = split_by_query(rows, seed=17)[1]
        assert [r["negative"] for r in first] == [r["negative"] for r in second]

    def test_a_different_seed_gives_a_different_split(self):
        rows = self._rows(n_queries=40)
        a = {r["query"] for r in split_by_query(rows, seed=1)[1]}
        b = {r["query"] for r in split_by_query(rows, seed=2)[1]}
        assert a != b

    def test_empty_input_does_not_explode(self):
        assert split_by_query([]) == ([], [])
