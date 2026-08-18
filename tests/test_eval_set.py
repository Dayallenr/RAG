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
    human_verified_count,
    load_eval_set,
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
