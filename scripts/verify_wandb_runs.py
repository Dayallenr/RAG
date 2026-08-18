"""
Verify the public experiment-tracking runs against the reports in ``results/``.

The README links a Weights & Biases project as third-party evidence that
these evaluations were really run — evidence that is worth more than a file
in this repository precisely because it is hosted elsewhere and cannot be
edited after the fact. This script is what stops that link from becoming a
claim nobody checks. It reads the project **with no credentials**, the way a
reader would, and compares every hosted metric against the report file on
disk, key for key.

It fails loudly on the two ways the link can go bad: the project turning
private (an anonymous read returns nothing), and a report being regenerated
without tracking on, so that the hosted run and the table in the README stop
agreeing. It also warns — without failing — when the project is set to
"Open" rather than "Public", because a run history strangers can add to is
weaker evidence than one they cannot.

Not part of CI: it needs the public internet and a third-party service, and
a tracking outage must never fail this repository's build. Run it by hand
when a report changes or before pointing anyone at the project.

Usage:
    python scripts/verify_wandb_runs.py
    python scripts/verify_wandb_runs.py --entity <entity> --project <project>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.track.verify import (
    DEFAULT_ENTITY,
    DEFAULT_PROJECT,
    RUN_REPORTS,
    LocalReport,
    ProjectNotPublicError,
    fetch_public_project,
    project_url,
    verify_runs,
)

DEFAULT_OUT = "results/tracking/report.json"

CAVEAT = (
    "Metrics are compared key for key against the report files in results/, using the "
    "same flattening that produced the hosted keys. The comparison says the hosted runs "
    "and the local reports agree; it does not re-derive the numbers from the corpus, and "
    "it inherits every caveat those reports state — most importantly that relevance "
    "labels are a floor, not an estimate."
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entity", default=DEFAULT_ENTITY)
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument(
        "--no-write", action="store_true", help="print the verdict, write no report"
    )
    args = parser.parse_args()

    reports = []
    for display_name, path in RUN_REPORTS.items():
        report_path = Path(path)
        if not report_path.exists():
            print(f"missing report {path} — run its eval first", file=sys.stderr)
            return 1
        reports.append(
            LocalReport(display_name, path, json.loads(report_path.read_text()))
        )

    print(f"reading {project_url(args.entity, args.project)} with no credentials…")
    try:
        project = fetch_public_project(args.entity, args.project)
    except ProjectNotPublicError as error:
        print(f"FAILED: {error}", file=sys.stderr)
        return 1

    result = verify_runs(
        project["runs"],
        reports,
        entity=project["entity"],
        project=project["project"],
        access=project["access"],
    )
    result["runs_on_server"] = project["run_count"]
    result["caveat"] = CAVEAT

    print(f"  anonymous read OK — {project['run_count']} runs on the server")
    print(f"  access: {result['access_note']}")
    if result["accepts_public_writes"]:
        # Not a failure — the reports still reproduce — but the reason to
        # cite a hosted run at all is that a stranger cannot write to it.
        print(
            "  WARNING: this is the 'Open' privacy setting, not 'Public'. Anyone signed\n"
            "           in to Weights & Biases can submit runs into this project. Switch\n"
            "           it to Public in the project's privacy settings to keep the run\n"
            "           history read-only to everyone but its owner."
        )
    print()
    for entry in result["runs"]:
        status = "ok  " if entry["ok"] else "FAIL"
        detail = entry.get("reason") or f"{entry['matched']}/{entry['compared']} metrics"
        print(f"  {status} {entry['display_name']:<18} {detail:<24} {entry['report']}")
        for bad in entry.get("mismatched", [])[:5]:
            print(f"         {bad['metric']}: hosted={bad['hosted']} local={bad['local']}")
        for missing in entry.get("missing_from_hosted", [])[:5]:
            print(f"         missing from the hosted run: {missing}")
        for extra in entry.get("only_in_hosted", [])[:5]:
            print(f"         only on the hosted run: {extra}")

    print(
        f"\n{result['metrics_matched']}/{result['metrics_compared']} hosted metrics match "
        f"results/ — verified={result['verified']}"
    )

    if not args.no_write:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2) + "\n")
        print(f"wrote {out}")

    return 0 if result["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
