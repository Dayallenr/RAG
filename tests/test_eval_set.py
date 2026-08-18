"""The one loader both the retrieval eval and the ablation sweep read through.

Two independent copies of this function used to exist. That made "the two
runs read the same questions" a convention rather than a guarantee — the
kind that holds right up until one copy is changed and the other is not.
"""
from __future__ import annotations

import json

import pytest

from duediligence.eval.eval_set import (
    DEFAULT_EVAL_SET_PATH,
    DEV,
    SPLITS,
    TEST,
    human_verified_count,
    load_eval_set,
    split_counts,
)


def _write(tmp_path, *rows):
    path = tmp_path / "eval_set.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    return str(path)


class TestLoadEvalSet:
    def test_reads_one_entry_per_line(self, tmp_path):
        path = _write(
            tmp_path,
            {"eval_id": "r001", "question": "a?", "relevant_chunk_ids": ["c1"]},
            {"eval_id": "r002", "question": "b?", "relevant_chunk_ids": ["c2"]},
        )
        entries = load_eval_set(path)
        assert [e["eval_id"] for e in entries] == ["r001", "r002"]

    def test_preserves_file_order(self, tmp_path):
        path = _write(tmp_path, *({"eval_id": f"r{i:03d}"} for i in range(5)))
        assert [e["eval_id"] for e in load_eval_set(path)] == [
            "r000", "r001", "r002", "r003", "r004"
        ]

    def test_blank_lines_are_skipped(self, tmp_path):
        path = tmp_path / "eval_set.jsonl"
        path.write_text('{"eval_id": "r001"}\n\n   \n{"eval_id": "r002"}\n\n')
        assert len(load_eval_set(str(path))) == 2

    def test_a_missing_file_is_a_hard_failure(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_eval_set(str(tmp_path / "absent.jsonl"))

    def test_the_default_path_is_the_tracked_eval_set(self):
        assert DEFAULT_EVAL_SET_PATH == "data/eval_set.jsonl"


class TestHumanVerifiedCount:
    """The honesty guard: a self-graded eval set must not be presentable as a
    curated one, so both consumers report how much of it a human checked."""

    def test_counts_only_entries_flagged_verified(self, tmp_path):
        path = _write(
            tmp_path,
            {"eval_id": "r001", "verified": True},
            {"eval_id": "r002", "verified": False},
            {"eval_id": "r003", "verified": True},
        )
        assert human_verified_count(load_eval_set(path)) == 2

    def test_a_missing_flag_counts_as_unverified(self, tmp_path):
        path = _write(tmp_path, {"eval_id": "r001"}, {"eval_id": "r002"})
        assert human_verified_count(load_eval_set(path)) == 0


class TestProvenanceField:
    """Every tracked eval row records how its question was drafted.

    The field is a real caveat on every metric scored against these
    questions — they were written while reading the chunk they are labelled
    against, so they reuse its vocabulary and structurally favour lexical
    matching. It stays recorded for that reason. What it does not do is name
    the tool that did the drafting, which says nothing about the numbers.
    ``verification_note`` is checked alongside it because a human writing
    free text is the likeliest place for the name to reappear.
    """

    TRACKED_EVAL_SETS = ["data/eval_set.jsonl", "data/routing_eval_set.jsonl"]

    @pytest.mark.parametrize("path", TRACKED_EVAL_SETS)
    def test_every_row_records_how_it_was_drafted(self, path):
        rows = load_eval_set(path)
        assert rows
        assert all(row.get("drafted_by", "").strip() for row in rows)

    @pytest.mark.parametrize("path", TRACKED_EVAL_SETS)
    def test_the_provenance_does_not_name_the_authoring_tool(self, path):
        for row in load_eval_set(path):
            free_text = f"{row.get('drafted_by', '')} {row.get('verification_note', '')}"
            assert "claude" not in free_text.lower(), row["eval_id"]


class TestSplitSelection:
    """The test split exists so a tuning decision cannot reach the questions
    the headline delta is reported on. That guarantee is only as good as the
    loader: a caller that asks for the development split and silently gets
    everything has no held-out set at all, it just believes it does."""

    def test_no_split_requested_returns_every_row(self, tmp_path):
        path = _write(
            tmp_path,
            {"eval_id": "r001", "split": DEV},
            {"eval_id": "r002", "split": TEST},
        )
        assert [e["eval_id"] for e in load_eval_set(path)] == ["r001", "r002"]

    def test_requesting_a_split_returns_exactly_that_split(self, tmp_path):
        path = _write(
            tmp_path,
            {"eval_id": "r001", "split": DEV},
            {"eval_id": "r002", "split": TEST},
            {"eval_id": "r003", "split": DEV},
        )
        assert [e["eval_id"] for e in load_eval_set(path, split=DEV)] == ["r001", "r003"]
        assert [e["eval_id"] for e in load_eval_set(path, split=TEST)] == ["r002"]

    def test_file_order_survives_filtering(self, tmp_path):
        rows = [{"eval_id": f"r{i:03d}", "split": DEV if i % 2 else TEST} for i in range(10)]
        path = _write(tmp_path, *rows)
        ids = [e["eval_id"] for e in load_eval_set(path, split=DEV)]
        assert ids == sorted(ids)

    def test_a_row_with_no_split_is_a_hard_failure_not_a_silent_drop(self, tmp_path):
        """The dangerous outcome is a quiet one. A row with no split either
        leaks into the held-out set or vanishes from both, and both look like
        a clean run."""
        path = _write(
            tmp_path,
            {"eval_id": "r001", "split": DEV},
            {"eval_id": "r002"},
        )
        with pytest.raises(ValueError, match="r002"):
            load_eval_set(path, split=DEV)

    def test_an_unsplit_row_is_fine_when_no_split_is_requested(self, tmp_path):
        path = _write(tmp_path, {"eval_id": "r001"}, {"eval_id": "r002"})
        assert len(load_eval_set(path)) == 2

    def test_an_unknown_split_name_raises(self, tmp_path):
        path = _write(tmp_path, {"eval_id": "r001", "split": DEV})
        with pytest.raises(ValueError, match="holdout"):
            load_eval_set(path, split="holdout")

    def test_the_split_names_are_the_two_the_project_uses(self):
        assert SPLITS == (DEV, TEST)


class TestSplitCounts:
    """Every report prints this, so a reader can tell which questions
    produced the number they are looking at."""

    def test_counts_rows_per_split(self, tmp_path):
        path = _write(
            tmp_path,
            {"eval_id": "r001", "split": DEV},
            {"eval_id": "r002", "split": TEST},
            {"eval_id": "r003", "split": DEV},
        )
        assert split_counts(load_eval_set(path)) == {DEV: 2, TEST: 1}

    def test_reports_both_splits_even_when_one_is_empty(self, tmp_path):
        path = _write(tmp_path, {"eval_id": "r001", "split": DEV})
        assert split_counts(load_eval_set(path)) == {DEV: 1, TEST: 0}

    def test_unassigned_rows_are_counted_separately_not_hidden(self, tmp_path):
        path = _write(
            tmp_path, {"eval_id": "r001", "split": DEV}, {"eval_id": "r002"}
        )
        assert split_counts(load_eval_set(path)) == {DEV: 1, TEST: 0, "unassigned": 1}
