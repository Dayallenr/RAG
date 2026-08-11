"""
Chart-understanding eval: qualitative, hand-graded — not a numeric-accuracy
score.

Precise chart digitization (reading an exact value off a bar) is a
genuinely unsolved CV problem; a harness that auto-scored "accuracy" here
would be manufacturing false precision. Instead, data/chart_eval_set.jsonl
holds hand-graded verdicts on three rubric criteria per chart
(chart_type_correct, trend_direction_correct, labels_correct) — each graded
by actually viewing the source image next to the generated description (see
each entry's grading_note for what was checked). This harness's job is
just to load and summarize those verdicts, not to invent an automated score
for something that isn't automatically scorable.

Usage:
    python -m duediligence.eval.run_chart_eval
"""
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["run_chart_eval"]

_CRITERIA = ("chart_type_correct", "trend_direction_correct", "labels_correct")


def run_chart_eval(eval_set_path: str = "data/chart_eval_set.jsonl") -> dict:
    entries = [
        json.loads(line) for line in Path(eval_set_path).read_text().splitlines() if line.strip()
    ]

    per_criterion = {
        criterion: sum(1 for e in entries if e[criterion]) for criterion in _CRITERIA
    }
    fully_correct = sum(1 for e in entries if all(e[c] for c in _CRITERIA))

    return {
        "total_graded": len(entries),
        "fully_correct": fully_correct,
        "fully_correct_rate": fully_correct / len(entries) if entries else 0.0,
        "per_criterion_correct": per_criterion,
        "note": (
            "Hand-graded against the source image, not an automated numeric-"
            "accuracy score — see each entry's grading_note in the eval set."
        ),
        "entries": entries,
    }


def main() -> None:
    report = run_chart_eval()

    output_path = Path("results/charts/report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")

    print(
        f"chart understanding: {report['fully_correct']}/{report['total_graded']} "
        f"fully correct on all 3 rubric criteria ({report['fully_correct_rate']:.0%})"
    )
    for criterion, count in report["per_criterion_correct"].items():
        print(f"  {criterion:26} {count}/{report['total_graded']}")
    print(f"\nwrote {output_path}")


if __name__ == "__main__":
    main()
