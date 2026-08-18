"""
Freeze a stratified development/test split onto data/eval_set.jsonl.

Writes a ``split`` field onto every row and leaves every other field exactly
as it found it. Rows that already carry a split keep it — running this again
is a no-op, and running it after the eval set grows tops the test split up
rather than re-drawing it. That is the whole point: a partition that can be
re-rolled is not a held-out set, it is a retry.

The assignment rules, and why, are in ``duediligence/eval/splits.py``.

Usage:
    python scripts/assign_eval_splits.py                 # apply
    python scripts/assign_eval_splits.py --dry-run       # show, write nothing
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.eval.eval_set import (
    DEFAULT_EVAL_SET_PATH,
    DEV,
    TEST,
    load_eval_set,
    split_counts,
)
from duediligence.eval.splits import DEFAULT_TEST_FRACTION, assign_splits, stratum_of


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", default=DEFAULT_EVAL_SET_PATH)
    parser.add_argument("--test-fraction", type=float, default=DEFAULT_TEST_FRACTION)
    parser.add_argument("--dry-run", action="store_true", help="print the split, write nothing")
    args = parser.parse_args()

    path = Path(args.eval_set)
    before = load_eval_set(str(path))
    after = assign_splits(before, test_fraction=args.test_fraction)

    newly_assigned = sum(
        1 for old, new in zip(before, after, strict=True) if old.get("split") != new["split"]
    )

    print(f"{path}: {len(after)} rows, {newly_assigned} newly assigned")
    print(f"  splits: {split_counts(after)}")
    print(f"  human-verified: {sum(1 for r in after if r.get('verified'))}")

    print(f"\n  {'question_type':<12}{'chunk_type':<20}{'dev':>6}{'test':>6}")
    per_stratum: dict[tuple[str, str], collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    for row in after:
        per_stratum[stratum_of(row)][row["split"]] += 1
    for (question_type, chunk_type), counts in sorted(per_stratum.items()):
        print(f"  {question_type:<12}{chunk_type:<20}{counts[DEV]:>6}{counts[TEST]:>6}")

    if args.dry_run:
        print("\ndry run — nothing written")
        return

    path.write_text("\n".join(json.dumps(row) for row in after) + "\n")
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
