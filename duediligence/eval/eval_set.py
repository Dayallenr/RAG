"""The single reader for ``data/eval_set.jsonl``.

Both the retrieval eval and the ablation sweep score against the same
questions, and both used to carry their own copy of this loader. That is
fine right up until the two copies disagree: a question set filtered one
way in the eval and another way in the ablations produces two clean-looking
reports that are not comparable, with no error and no warning to say so.
One loader makes "these ran over the same questions" true by construction
rather than by convention.

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

__all__ = ["DEFAULT_EVAL_SET_PATH", "human_verified_count", "load_eval_set"]

DEFAULT_EVAL_SET_PATH = "data/eval_set.jsonl"


def load_eval_set(path: str = DEFAULT_EVAL_SET_PATH) -> list[dict]:
    """Read the evaluation set, one JSON object per line, in file order.

    Order is load-bearing: callers embed the questions in one batch and then
    ``zip`` the vectors back against the entries.
    """
    lines = Path(path).read_text().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def human_verified_count(entries: Iterable[dict]) -> int:
    """How many entries a human has actually checked.

    Every report prints this next to its metrics. The eval questions were
    drafted mechanically from sampled chunks, so a run over an unverified
    set is a self-graded one — which is a legitimate thing to publish, but
    not a legitimate thing to publish silently.
    """
    return sum(1 for entry in entries if entry.get("verified"))
