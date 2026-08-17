"""
Fold a completed co-validity review sheet back into the eval set.

Reads the ticked checkboxes from ``data/eval_covalidity_review.md`` and adds
those chunk ids to the matching question's ``relevant_chunk_ids``. Existing
labels are never removed — this pass only ever *widens* a label, because the
premise of the review is that the current label is already correct and the
question is what else answers alongside it.

Refuses to invent labels: a ticked id that was not among the candidates
offered for that question is rejected rather than silently accepted, since
that means the sheet and the eval set have drifted apart and the safe
assumption is that the sheet is stale.

Idempotent — running it twice adds nothing the second time, so a partially
reviewed sheet can be applied, extended, and applied again.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# "### `r004` — question text"
_HEADING_RE = re.compile(r"^###\s+`([^`]+)`")
# "- [x] `abc123` — rank 1 · ..."  (accepts x or X)
_TICKED_RE = re.compile(r"^-\s*\[[xX]\]\s*`([0-9a-f]+)`")


def parse_review(markdown: str) -> dict[str, list[str]]:
    """eval_id -> the chunk ids ticked under it."""
    ticked: dict[str, list[str]] = {}
    current: str | None = None
    for line in markdown.splitlines():
        heading = _HEADING_RE.match(line)
        if heading:
            current = heading.group(1)
            ticked.setdefault(current, [])
            continue
        match = _TICKED_RE.match(line.strip())
        if match and current is not None:
            ticked[current].append(match.group(1))
    return ticked


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", default="data/eval_covalidity_review.md")
    parser.add_argument("--candidates", default="data/eval_covalidity_candidates.jsonl")
    parser.add_argument("--eval-set", default="data/eval_set.jsonl")
    parser.add_argument("--note", default="co-validity pass: additional answering chunks added")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ticked = parse_review(Path(args.review).read_text())
    offered = {
        row["eval_id"]: set(row["candidate_chunk_ids"])
        for row in (
            json.loads(line)
            for line in Path(args.candidates).read_text().splitlines()
            if line.strip()
        )
    }

    entries = [
        json.loads(line)
        for line in Path(args.eval_set).read_text().splitlines()
        if line.strip()
    ]

    added_total = 0
    touched = 0
    rejected: list[tuple[str, str]] = []

    for entry in entries:
        eval_id = entry["eval_id"]
        picks = ticked.get(eval_id)
        if not picks:
            continue

        valid = []
        for chunk_id in picks:
            if chunk_id in offered.get(eval_id, set()):
                valid.append(chunk_id)
            else:
                rejected.append((eval_id, chunk_id))

        existing = entry.get("relevant_chunk_ids", [])
        new = [c for c in valid if c not in existing]
        if not new:
            continue

        entry["relevant_chunk_ids"] = existing + new
        note = entry.get("verification_note") or ""
        entry["verification_note"] = (
            f"{note}; {args.note} (+{len(new)})" if note else f"{args.note} (+{len(new)})"
        )
        added_total += len(new)
        touched += 1

    if rejected:
        print("REJECTED — ticked but not offered as a candidate for that question:")
        for eval_id, chunk_id in rejected:
            print(f"  {eval_id}: {chunk_id}")
        print("  (the review sheet and the eval set have drifted — regenerate the sheet)\n")

    label_counts = [len(e.get("relevant_chunk_ids", [])) for e in entries]
    print(f"questions widened: {touched}")
    print(f"chunk ids added:   {added_total}")
    print(f"mean labels/question: {sum(label_counts) / len(label_counts):.2f}")
    print(f"questions with >1 label: {sum(1 for n in label_counts if n > 1)}/{len(entries)}")

    if args.dry_run:
        print("\ndry run — nothing written")
        return

    with Path(args.eval_set).open("w") as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + "\n")
    print(f"\nwrote {args.eval_set}")
    print("re-run: python -m duediligence.eval.run_retrieval_eval")


if __name__ == "__main__":
    main()
