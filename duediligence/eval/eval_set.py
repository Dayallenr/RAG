"""The single reader for ``data/eval_set.jsonl``.

Both the retrieval eval and the ablation sweep score against the same
questions, and both used to carry their own copy of this loader. That is
fine right up until the two copies disagree: a question set filtered one
way in the eval and another way in the ablations produces two clean-looking
reports that are not comparable, with no error and no warning to say so.
One loader makes "these ran over the same questions" true by construction
rather than by convention.

Rows also carry a ``split``. The fusion weight was selected by sweeping
against the same questions the headline numbers are reported on, so a
fine-tune delta stacked on top of that would rest on a figure optimised
against twice. The split is a field on the row rather than a second file
because two files drift: a question can be edited in one and not the other,
and nothing detects it. One file, one row, one split.

The entries stay plain dicts. The eval set gains fields over time
(``verified``, ``verification_note``) and every consumer reads a different
subset of them, so a typed record here would mean editing this module every
time the file grows a column, for no checking that the callers do not
already do.
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

__all__ = [
    "DEFAULT_EVAL_SET_PATH", "DEV", "SPLITS", "TEST",
    "human_verified_count", "load_eval_set", "split_counts",
]

DEFAULT_EVAL_SET_PATH = "data/eval_set.jsonl"

#: Tuning decisions — fusion weight, rerank depth, chunk levels — are swept
#: against DEV. TEST is scored once, at the end, and never swept against.
DEV = "dev"
TEST = "test"
SPLITS = (DEV, TEST)


def load_eval_set(path: str = DEFAULT_EVAL_SET_PATH, *, split: str | None = None) -> list[dict]:
    """Read the evaluation set, one JSON object per line, in file order.

    Order is load-bearing: callers embed the questions in one batch and then
    ``zip`` the vectors back against the entries.

    ``split=None`` returns every row, which is what reproduces the published
    full-set comparison table. Naming a split returns exactly that split's
    rows, still in file order.

    A row carrying no split is an error *when a split is requested*, and only
    then. There is no safe default for it: treating it as development leaks
    an unexamined question into the tuning set, and dropping it silently
    shrinks the eval without saying so. Both produce a report that looks
    clean and is not, so this raises instead.
    """
    lines = Path(path).read_text().splitlines()
    entries = [json.loads(line) for line in lines if line.strip()]
    if split is None:
        return entries
    if split not in SPLITS:
        raise ValueError(f"unknown split {split!r}; known splits: {list(SPLITS)}")
    unassigned = [e.get("eval_id", "<no eval_id>") for e in entries if not e.get("split")]
    if unassigned:
        raise ValueError(
            f"{len(unassigned)} row(s) in {path} carry no split and cannot be "
            f"assigned to one here: {unassigned[:10]}"
            + (" ..." if len(unassigned) > 10 else "")
            + " — run scripts/assign_eval_splits.py"
        )
    return [e for e in entries if e["split"] == split]


def split_counts(entries: Iterable[dict]) -> dict[str, int]:
    """How many questions each split holds, for a report to record.

    Both splits are always present, including at zero, so a reader can tell
    an empty split from a report written before splits existed. Rows with no
    split are counted under their own key rather than folded into either.
    """
    counts = {DEV: 0, TEST: 0}
    for entry in entries:
        value = entry.get("split")
        if value in counts:
            counts[value] += 1
        else:
            counts["unassigned"] = counts.get("unassigned", 0) + 1
    return counts


def human_verified_count(entries: Iterable[dict]) -> int:
    """How many entries a human has actually checked.

    Every report prints this next to its metrics. The eval questions were
    drafted mechanically from sampled chunks, so a run over an unverified
    set is a self-graded one — which is a legitimate thing to publish, but
    not a legitimate thing to publish silently.
    """
    return sum(1 for entry in entries if entry.get("verified"))
