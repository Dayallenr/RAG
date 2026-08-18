"""Stratified, frozen assignment of eval rows to a development or test split.

These tests assert the *properties* the split has to hold — representative,
verified-only, frozen once written — rather than a specific partition. A test
pinning the exact 30 questions would fail the moment the eval set grows by one
row, which is a change the design is supposed to accommodate, and would have to
be updated by pasting in whatever the code just produced. That is not a test.
"""
from __future__ import annotations

import collections

import pytest

from duediligence.eval.eval_set import DEV, TEST
from duediligence.eval.splits import assign_splits


def _rows(n, *, question_type="table", chunk_type="table", verified=True, start=0):
    return [
        {
            "eval_id": f"r{i:03d}",
            "question_type": question_type,
            "chunk_type": chunk_type,
            "verified": verified,
        }
        for i in range(start, start + n)
    ]


def _by_id(rows):
    return {r["eval_id"]: r for r in rows}


class TestEveryRowIsAssigned:
    def test_every_row_comes_back_with_a_split(self):
        assigned = assign_splits(_rows(20))
        assert all(row["split"] in (DEV, TEST) for row in assigned)

    def test_row_order_is_preserved(self):
        rows = _rows(20)
        assigned = assign_splits(rows)
        assert [r["eval_id"] for r in assigned] == [r["eval_id"] for r in rows]

    def test_the_input_rows_are_not_mutated(self):
        rows = _rows(10)
        assign_splits(rows)
        assert all("split" not in row for row in rows)


class TestVerifiedOnly:
    """An unverified question has never been read by a human. Scoring the
    headline delta on one means the number rests on a label nobody checked."""

    def test_unverified_rows_never_land_in_test(self):
        rows = _rows(10, verified=True) + _rows(10, verified=False, start=100)
        assigned = assign_splits(rows)
        for row in assigned:
            if not row["verified"]:
                assert row["split"] == DEV

    def test_a_missing_verified_flag_is_treated_as_unverified(self):
        rows = _rows(10)
        for row in rows:
            del row["verified"]
        assigned = assign_splits(rows)
        assert all(row["split"] == DEV for row in assigned)


class TestStratification:
    def test_each_stratum_contributes_to_test_roughly_in_proportion(self):
        rows = (
            _rows(40, question_type="table", chunk_type="table", start=0)
            + _rows(20, question_type="narrative", chunk_type="paragraph", start=100)
            + _rows(20, question_type="numeric", chunk_type="section", start=200)
        )
        assigned = assign_splits(rows, test_fraction=0.3)
        per_stratum = collections.Counter(
            (r["question_type"], r["chunk_type"]) for r in assigned if r["split"] == TEST
        )
        assert per_stratum[("table", "table")] == 12
        assert per_stratum[("narrative", "paragraph")] == 6
        assert per_stratum[("numeric", "section")] == 6

    def test_no_stratum_is_swallowed_whole_by_one_split(self):
        """The failure this prevents is a test set that is accidentally all
        tables — representative of nothing, and trivially beaten or lost by a
        model that happens to be good or bad at one chunk type."""
        rows = (
            _rows(10, question_type="table", chunk_type="table", start=0)
            + _rows(10, question_type="chart", chunk_type="chart_description", start=100)
        )
        assigned = assign_splits(rows, test_fraction=0.3)
        strata_in_test = {
            (r["question_type"], r["chunk_type"]) for r in assigned if r["split"] == TEST
        }
        assert len(strata_in_test) == 2

    def test_a_stratum_too_small_to_split_stays_in_development(self):
        rows = _rows(1, question_type="narrative", chunk_type="document")
        assert assign_splits(rows, test_fraction=0.3)[0]["split"] == DEV


class TestFrozen:
    """Re-running assignment must not reshuffle the partition. If it can, then
    any run that produces a disappointing number can be followed by another
    run that produces a better one, and the split has stopped meaning
    anything."""

    def test_rerunning_on_an_already_split_file_changes_nothing(self):
        first = assign_splits(_rows(60))
        second = assign_splits(first)
        assert _by_id(second) == _by_id(first)

    def test_existing_assignments_survive_new_rows_being_added(self):
        first = assign_splits(_rows(60))
        grown = assign_splits(first + _rows(40, start=500))
        for eval_id, row in _by_id(first).items():
            assert _by_id(grown)[eval_id]["split"] == row["split"]

    def test_new_rows_are_assigned_toward_the_target_proportion(self):
        first = assign_splits(_rows(60), test_fraction=0.3)
        grown = assign_splits(first + _rows(40, start=500), test_fraction=0.3)
        assert sum(1 for r in grown if r["split"] == TEST) == 30

    def test_assignment_does_not_depend_on_row_order(self):
        rows = _rows(60)
        forward = _by_id(assign_splits(rows))
        backward = _by_id(assign_splits(list(reversed(rows))))
        assert {k: v["split"] for k, v in forward.items()} == {
            k: v["split"] for k, v in backward.items()
        }

    def test_an_unrecognised_split_value_is_rejected_rather_than_overwritten(self):
        rows = _rows(5)
        rows[0]["split"] = "holdout"
        with pytest.raises(ValueError, match="holdout"):
            assign_splits(rows)


class TestTestFraction:
    def test_a_fraction_outside_the_unit_interval_is_rejected(self):
        for bad in (-0.1, 1.0, 1.5):
            with pytest.raises(ValueError):
                assign_splits(_rows(10), test_fraction=bad)


class TestExplicitNullSplit:
    """A hand-edited row can carry ``"split": null`` — the key is present, so
    a default-if-absent assignment would step over it and leave the row in
    neither split."""

    def test_a_null_split_is_assigned_like_a_missing_one(self):
        rows = _rows(10)
        for row in rows:
            row["split"] = None
        assigned = assign_splits(rows)
        assert all(row["split"] in (DEV, TEST) for row in assigned)
        assert sum(1 for r in assigned if r["split"] == TEST) == 3
