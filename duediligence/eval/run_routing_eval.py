"""
Routing eval: two things measured, not one.

**1. Classification accuracy** — does ``classify_query`` send each query
down the right path? Scored against ``data/routing_eval_set.jsonl``.
Reported as a confusion matrix rather than a single accuracy number,
because the two error types are not equally bad:

* *false structured* (a narrative question sent to exact lookup) is the
  dangerous one — it answers with an authoritative figure for a question
  that wanted an explanation.
* *false semantic* (a lookup question sent to search) merely gives up an
  exactness guarantee and returns passages, which a user can still read.

The router is deliberately biased toward the second, so the interesting
number is **structured-route precision**, not overall accuracy.

**2. End-to-end exactness** — for queries routed to structured lookup, is
the returned value right? Scored against ``data/extraction_eval_set.jsonl``,
whose three entries are hand-verified against the filings' own MD&A prose.
This is the only eval in the project with an unambiguous right answer, and
it is what makes the structured route worth having: a number that is either
exactly correct or explicitly absent.

Usage:
    python -m duediligence.eval.run_routing_eval
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from duediligence.route.query_router import classify_query
from duediligence.route.structured_lookup import lookup_fact
from duediligence.track import flatten_metrics, log_run

__all__ = ["run_routing_eval"]


def _load(path: str) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def evaluate_classification(entries: list[dict]) -> dict:
    confusion: Counter = Counter()
    rows = []
    for entry in entries:
        decision = classify_query(entry["question"])
        predicted = decision.route.value
        expected = entry["expected_route"]
        confusion[(expected, predicted)] += 1
        rows.append(
            {
                "eval_id": entry["eval_id"],
                "question": entry["question"],
                "expected_route": expected,
                "predicted_route": predicted,
                "correct": predicted == expected,
                "concept": decision.concept,
                "company": decision.company,
                "fiscal_year": decision.fiscal_year,
                "reasons": decision.reasons,
            }
        )

    correct = sum(1 for r in rows if r["correct"])
    true_structured = confusion[("structured", "structured")]
    false_structured = confusion[("semantic", "structured")]
    false_semantic = confusion[("structured", "semantic")]

    return {
        "total": len(rows),
        "correct": correct,
        "accuracy": correct / len(rows) if rows else 0.0,
        "confusion": {f"{e}->{p}": n for (e, p), n in sorted(confusion.items())},
        # The metric that matters: of everything sent to exact lookup, how
        # much of it genuinely belonged there.
        "structured_precision": (
            true_structured / (true_structured + false_structured)
            if (true_structured + false_structured)
            else None
        ),
        "structured_recall": (
            true_structured / (true_structured + false_semantic)
            if (true_structured + false_semantic)
            else None
        ),
        "results": rows,
    }


def evaluate_exactness(entries: list[dict]) -> dict:
    """Does the structured route return the hand-verified value?"""
    rows = []
    for entry in entries:
        # These entries are (company, concept, expected_value) triples; the
        # fiscal year comes from the verification note's period, which for
        # every current entry is FY2023.
        fiscal_year = entry.get("fiscal_year", 2023)
        answer = lookup_fact(entry["concept"], entry["company"], fiscal_year)
        passed = answer is not None and abs(answer.value - entry["expected_value"]) < 1.0
        rows.append(
            {
                "eval_id": entry["eval_id"],
                "company": entry["company"],
                "concept": entry["concept"],
                "fiscal_year": fiscal_year,
                "expected_value": entry["expected_value"],
                "actual_value": answer.value if answer else None,
                "accession_number": answer.accession_number if answer else None,
                "period": f"{answer.period_start}..{answer.period_end}" if answer else None,
                "passed": passed,
            }
        )
    passed = sum(1 for r in rows if r["passed"])
    return {
        "total": len(rows),
        "passed": passed,
        "accuracy": passed / len(rows) if rows else 0.0,
        "results": rows,
    }


def run_routing_eval(
    routing_set: str = "data/routing_eval_set.jsonl",
    extraction_set: str = "data/extraction_eval_set.jsonl",
) -> dict:
    routing_entries = _load(routing_set)
    return {
        "routing_eval_set": routing_set,
        "classification_caveat": (
            "The routing eval set and the routing rules were written by the same author, "
            "so a high classification score demonstrates internal consistency rather than "
            "generalization to queries phrased in ways the rules did not anticipate. Treat "
            "it as a regression test, not evidence of real-world routing accuracy. The "
            "exactness section is different: it scores against hand-verified XBRL ground "
            "truth checked independently against the filings' own MD&A prose."
        ),
        "human_verified_routing_queries": sum(
            1 for e in routing_entries if e.get("verified")
        ),
        "classification": evaluate_classification(routing_entries),
        "exactness": evaluate_exactness(_load(extraction_set)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="results/routing/report.json")
    args = parser.parse_args()

    report = run_routing_eval()
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")

    run_url = log_run(
        name="routing-eval",
        tags=["routing", "eval"],
        config={"eval_set": "data/routing_eval_set.jsonl"},
        metrics=flatten_metrics(report),
    )
    if run_url:
        print(f"tracked: {run_url}\n")

    classification = report["classification"]
    print(
        f"routing classification: {classification['correct']}/{classification['total']} "
        f"({classification['accuracy']:.1%})"
    )
    print(f"  confusion: {classification['confusion']}")
    precision = classification["structured_precision"]
    recall = classification["structured_recall"]
    print(
        f"  structured precision: {precision:.1%}" if precision is not None else "  structured precision: n/a"
    )
    print(f"  structured recall:    {recall:.1%}" if recall is not None else "  structured recall: n/a")

    for row in classification["results"]:
        if not row["correct"]:
            print(f"  MISROUTED [{row['expected_route']} -> {row['predicted_route']}] {row['question']}")

    exactness = report["exactness"]
    print(
        f"\nstructured exactness vs hand-verified XBRL: "
        f"{exactness['passed']}/{exactness['total']} ({exactness['accuracy']:.1%})"
    )
    for row in exactness["results"]:
        marker = "PASS" if row["passed"] else "FAIL"
        print(
            f"  [{marker}] {row['company']} {row['concept']} FY{row['fiscal_year']}: "
            f"{row['actual_value']:,.0f}" if row["actual_value"] else f"  [{marker}] {row['eval_id']}: no data"
        )

    if report["human_verified_routing_queries"] == 0:
        print(
            "\nNOTE: the routing eval set and the routing rules share an author, so the "
            "classification score above is a regression test, not evidence of real-world "
            "routing accuracy. The exactness figures ARE independently grounded — they "
            "score against data/extraction_eval_set.jsonl, verified against filing prose."
        )
    print(f"\nwrote {output}")


if __name__ == "__main__":
    main()
