"""
Extraction-accuracy eval: does a structured XBRL fact match what the same
filing's own narrative prose says?

This is the one eval in the whole project where "correct" has an
unambiguous right answer — unlike retrieval relevance or answer
groundedness, a dollar figure either matches the filing or it doesn't. Each
entry in data/extraction_eval_set.jsonl was verified by finding the
concept's value stated in prose (usually the Item 7 MD&A section) and
confirming it against the corresponding extracted XBRL fact — see each
entry's ``verification_note`` for exactly what was checked and where.

This eval set is intentionally small (a handful of entries across two
companies) and XBRL-only — a real next step, better done by a person
looking at the source filing directly, is extending it with more entries
and adding table-cell checks (verifying a parsed table cell against the
rendered table in the filing, which this harness's ``type`` field already
supports the shape for, just not yet populated).

Usage:
    python -m duediligence.eval.run_extraction_eval
"""
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["run_extraction_eval"]

# Exact-match in principle (XBRL values are exact integers/dollars), but a
# tiny relative tolerance absorbs any float round-tripping through JSON.
_RELATIVE_TOLERANCE = 1e-6


def _load_facts(company: str) -> list[dict]:
    path = Path(f"data/facts/{company}.jsonl")
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _check_xbrl_entry(entry: dict, facts_by_company: dict[str, list[dict]]) -> dict:
    facts = facts_by_company.setdefault(entry["company"], _load_facts(entry["company"]))
    matches = [
        f for f in facts
        if f["concept"] == entry["concept"] and f["accession_number"] == entry["accession_number"]
    ]

    if not matches:
        return {**entry, "status": "fact_not_found", "actual_value": None, "passed": False}

    # A (concept, accession) pair can have several period-tagged entries
    # (e.g. quarterly breakdowns reported inside an annual filing) — take
    # the one closest to the expected value rather than assuming order.
    closest = min(matches, key=lambda f: abs(f["value"] - entry["expected_value"]))
    relative_error = abs(closest["value"] - entry["expected_value"]) / abs(entry["expected_value"])
    passed = relative_error <= _RELATIVE_TOLERANCE

    return {
        **entry, "status": "checked", "actual_value": closest["value"],
        "relative_error": relative_error, "passed": passed,
    }


def run_extraction_eval(eval_set_path: str = "data/extraction_eval_set.jsonl") -> dict:
    entries = [
        json.loads(line) for line in Path(eval_set_path).read_text().splitlines() if line.strip()
    ]

    facts_by_company: dict[str, list[dict]] = {}
    results = []
    for entry in entries:
        if entry["type"] == "xbrl":
            results.append(_check_xbrl_entry(entry, facts_by_company))
        else:
            results.append({**entry, "status": "unsupported_type", "passed": False})

    passed = sum(1 for r in results if r["passed"])
    return {
        "total": len(results),
        "passed": passed,
        "accuracy": passed / len(results) if results else 0.0,
        "results": results,
    }


def main() -> None:
    report = run_extraction_eval()

    output_path = Path("results/extraction/report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")

    print(f"extraction accuracy: {report['passed']}/{report['total']} ({report['accuracy']:.1%})")
    for result in report["results"]:
        marker = "PASS" if result["passed"] else "FAIL"
        print(f"  [{marker}] {result['eval_id']}: {result['company']} {result.get('concept', '?')}")
    print(f"\nwrote {output_path}")


if __name__ == "__main__":
    main()
