"""Tests for hard-negative mining and the training split."""
from __future__ import annotations

from duediligence.train.mine import (
    normalize_company_names,
    select_negatives,
    split_by_query,
    text_key,
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


class TestTextKey:
    def test_case_and_whitespace_are_ignored(self):
        assert text_key("  The\nSame   Text ") == text_key("the same text")

    def test_different_text_gives_a_different_key(self):
        assert text_key("net income rose") != text_key("net income fell")

    def test_whitespace_only_text_is_empty(self):
        assert text_key("   \n\t ") == ""


class TestSelectNegatives:
    def _candidates(self, *ids):
        # Distinct text per id unless a test says otherwise.
        return [(cid, f"passage {cid}") for cid in ids]

    def test_excludes_the_positive(self):
        # Training the model to push away a passage that answers the query
        # would be actively harmful.
        got = select_negatives(self._candidates("a", "p", "b", "c"), "p", "passage p", n=3)
        assert "p" not in got

    def test_excludes_a_negative_identical_to_the_positive(self):
        # The real defect: ids are not purely content-addressed, so the same
        # boilerplate paragraph exists under several of them and an id-only
        # check readmits the positive's own twin.
        boilerplate = "Holders of our common stock are only entitled to dividends."
        candidates = [("twin", boilerplate), ("b", "something else")]
        assert select_negatives(candidates, "p", boilerplate, n=3) == ["b"]

    def test_identical_text_is_matched_despite_case_and_whitespace(self):
        candidates = [("twin", "  THE   Same\nText "), ("b", "different")]
        assert select_negatives(candidates, "p", "the same text", n=3) == ["b"]

    def test_deduplicates_negatives_against_each_other(self):
        # Two byte-identical negatives spend two slots on one example.
        candidates = [("a", "repeated"), ("b", "repeated"), ("c", "distinct")]
        assert select_negatives(candidates, "p", "positive", n=3) == ["a", "c"]

    def test_skips_empty_chunks(self):
        candidates = [("a", "   "), ("b", "real text")]
        assert select_negatives(candidates, "p", "positive", n=3) == ["b"]

    def test_returns_the_requested_count(self):
        got = select_negatives(self._candidates("a", "b", "c", "d", "e"), "p", "pos", n=3)
        assert len(got) == 3

    def test_preserves_retrieval_order(self):
        assert select_negatives(self._candidates("a", "b", "c"), "p", "pos", n=2) == ["a", "b"]

    def test_skip_top_drops_the_hardest_hits(self):
        # The top non-positive hit is sometimes a genuine near-duplicate —
        # the same event reported in both companies' filings.
        got = select_negatives(self._candidates("a", "b", "c", "d"), "p", "pos", n=2, skip_top=1)
        assert got == ["b", "c"]

    def test_skip_top_counts_surviving_hits_not_raw_ones(self):
        # "a" is filtered as the positive's twin, so skip_top=1 must drop
        # "b" — the hardest hit that was actually usable.
        candidates = [("a", "pos"), ("b", "one"), ("c", "two"), ("d", "three")]
        assert select_negatives(candidates, "p", "pos", n=2, skip_top=1) == ["c", "d"]

    def test_handles_fewer_candidates_than_requested(self):
        assert select_negatives(self._candidates("a"), "p", "pos", n=5) == ["a"]

    def test_handles_a_result_list_of_only_the_positive(self):
        assert select_negatives([("p", "pos")], "p", "pos", n=3) == []

    def test_excludes_another_positive_of_the_same_query(self):
        # A generic question gets generated from two filings, so a passage
        # that is one copy's positive must not be the other copy's negative.
        other_positive = "The Company is subject to capital adequacy guidelines."
        candidates = [("a", other_positive), ("b", "unrelated passage")]
        got = select_negatives(
            candidates, "p", "positive text", n=3, also_exclude=[other_positive]
        )
        assert got == ["b"]

    def test_also_exclude_ignores_blank_entries(self):
        candidates = [("a", "one"), ("b", "two")]
        assert select_negatives(candidates, "p", "pos", n=2, also_exclude=["", "  "]) == [
            "a",
            "b",
        ]

    def test_an_empty_positive_does_not_filter_everything(self):
        # A missing positive text must not make every empty-keyed candidate
        # collide with it.
        assert select_negatives(self._candidates("a", "b"), "p", "", n=2) == ["a", "b"]


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
