"""Assign every evaluation row to a development or test split.

Why this exists at all: the fusion weight reported in the ablations was
selected by sweeping against the same 101 questions the headline retrieval
table is scored on. That is a stated, bounded optimism as long as it is the
only such choice. Stacking a fine-tune delta on top of it would rest the
project's central ML claim on a figure that has been optimised against twice,
and no caveat rescues that — the number would simply not mean what it says.

Three properties make the split worth trusting, and each is a test:

*Stratified* across question type and chunk type, so the test set is
representative rather than accidentally all tables. Retrieval quality varies
sharply by chunk type here — BM25 recall@10 runs 0.42 on tables against 1.00
on chart descriptions — so an unstratified draw could shift the headline by
more than any model change would.

*Verified only*, because an unverified label has never been read by a human
and the test split is the one number nobody gets to re-run.

*Frozen*, because assignment that reshuffles is not a held-out set. Rows that
already carry a split keep it, so a later verification pass can extend the
eval set without re-drawing the partition into a more favourable one.
"""
from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Iterable

from duediligence.eval.eval_set import DEV, SPLITS, TEST

__all__ = ["DEFAULT_TEST_FRACTION", "assign_splits", "stratum_of"]

#: 30% held out. Small in absolute terms — around 30 questions — which is a
#: real limitation on the resolution of any delta measured against it, and one
#: every report using this split has to keep stating. Held out anyway: a
#: contaminated 101 answers a different, easier question than an honest 30.
DEFAULT_TEST_FRACTION = 0.3


def stratum_of(entry: dict) -> tuple[str, str]:
    """The cell an entry belongs to. Question type and chunk type together —
    they are correlated but not redundant (a numeric question can be labelled
    against a paragraph or a table, and those retrieve very differently)."""
    return (entry.get("question_type", ""), entry.get("chunk_type", ""))


def _draw_order(eval_id: str) -> str:
    """Deterministic, stable, and uncorrelated with anything in the file.

    Sorting by ``eval_id`` directly would draw the test set from whichever
    companies happen to sort first, because ids were assigned in corpus order.
    Hashing decorrelates it while keeping the choice reproducible from the id
    alone — so the same row draws the same way no matter what else is in the
    file, which is what lets the set grow without reshuffling.
    """
    return hashlib.sha256(eval_id.encode()).hexdigest()


def assign_splits(
    entries: Iterable[dict],
    *,
    test_fraction: float = DEFAULT_TEST_FRACTION,
) -> list[dict]:
    """Return copies of ``entries``, each carrying a ``split``.

    Existing assignments are never changed. Only rows without one are drawn,
    and they are drawn toward the proportion the whole stratum should have,
    counting what is already assigned — so adding rows later tops the test
    split up rather than rebuilding it.
    """
    if not 0.0 <= test_fraction < 1.0:
        raise ValueError(f"test_fraction must be in [0.0, 1.0), got {test_fraction}")

    rows = [dict(entry) for entry in entries]

    for row in rows:
        existing = row.get("split")
        if existing is not None and existing not in SPLITS:
            raise ValueError(
                f"row {row.get('eval_id')!r} carries unrecognised split {existing!r}; "
                f"known splits: {list(SPLITS)}. Refusing to overwrite it — an "
                "unexpected value is a sign of a hand edit, not something to clobber."
            )

    by_stratum: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        by_stratum[stratum_of(row)].append(row)

    for stratum_rows in by_stratum.values():
        # Only verified rows are eligible for test, so they are also the only
        # rows the target proportion is computed over. Sizing the target off
        # the full stratum would over-draw from a partly-verified one.
        verified = [r for r in stratum_rows if r.get("verified")]
        already_test = sum(1 for r in verified if r.get("split") == TEST)
        target_test = round(len(verified) * test_fraction)

        eligible = sorted(
            (r for r in verified if r.get("split") is None),
            key=lambda r: _draw_order(r.get("eval_id", "")),
        )
        for row in eligible[: max(0, target_test - already_test)]:
            row["split"] = TEST

        for row in stratum_rows:
            # Not setdefault: a row carrying an explicit null split has the
            # key already, and setdefault would leave it unassigned.
            if row.get("split") is None:
                row["split"] = DEV

    return rows
