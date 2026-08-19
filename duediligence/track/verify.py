"""
Check that the hosted experiment-tracking runs still say what ``results/``
says — reading them the way a stranger would, with no credentials.

Why this exists: the README points a reader at a Weights & Biases project as
third-party evidence that these evaluations were really run. That link is
only worth something if two things hold, and neither is self-evident from
the repository:

1. **The project is readable without an account.** A private project is a
   dead link to everyone but its owner. The check is structural rather than
   cosmetic — Weights & Biases' GraphQL API returns ``project: null`` to an
   anonymous caller when a project is private, so a successful anonymous
   read *is* the visibility test. This module therefore never sends a
   credential, even when ``WANDB_API_KEY`` sits in the environment; doing so
   would make a private project look public, which is the one way this check
   could certify something false.
2. **The hosted numbers are the same numbers.** ``results/*.json`` is
   rewritten by every re-run, and the hosted run is not. They drift the
   moment a report is regenerated without tracking enabled — at which point
   the README cites a run that disagrees with the table beside it.

The comparison reuses :func:`duediligence.track.experiment.flatten_metrics`,
the same function that produced the hosted keys in the first place, so this
compares like with like instead of a second, drifting idea of what the
report's metric names are.

A missing metric fails. Zero shared metrics fails. An empty run must never
score as "everything matched".
"""
from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from duediligence.track.experiment import DEFAULT_PROJECT, flatten_metrics

__all__ = [
    "DEFAULT_ENTITY",
    "DEFAULT_PROJECT",
    "DEFAULT_TOLERANCE",
    "LocalReport",
    "ProjectNotPublicError",
    "RUN_REPORTS",
    "accepts_public_writes",
    "compare_run",
    "describe_access",
    "fetch_public_project",
    "latest_finished_runs",
    "project_url",
    "verify_runs",
]

WANDB_GRAPHQL_URL = "https://api.wandb.ai/graphql"
DEFAULT_ENTITY = "dayallenr30-university-of-california"

# Hosted metrics are logged as float64 and come back as float64, so in
# practice these compare exactly. The tolerance is here so a future rounding
# change in the transport is a rounding change, not a false alarm.
DEFAULT_TOLERANCE = 1e-9

# Which run name carries which report. The run name is set by the eval
# scripts at ``log_run(name=...)``; the mapping is spelled out here rather
# than inferred so a renamed run fails loudly instead of quietly dropping a
# report from the check.
RUN_REPORTS: dict[str, str] = {
    "training": "results/training/report.json",
    "retrieval-eval": "results/retrieval/report.json",
    "ablations": "results/ablations/report.json",
    "routing-eval": "results/routing/report.json",
    "groundedness-eval": "results/generation/report.json",
    # The fine-tune delta and the four runs it subtracts. The cells are
    # registered individually rather than only through the comparison: a cell
    # scored against the wrong index still produces a clean-looking delta, and
    # the only way that shows up here is if each cell's hosted metrics are
    # diffed against the report file that named its index.
    "finetune-delta": "results/finetune_delta/report.json",
    "finetune-delta-base-norerank": "results/finetune_delta/base-norerank.json",
    "finetune-delta-base-rerank": "results/finetune_delta/base-rerank.json",
    "finetune-delta-finetuned-norerank": "results/finetune_delta/finetuned-norerank.json",
    "finetune-delta-finetuned-rerank": "results/finetune_delta/finetuned-rerank.json",
}

# ``runs(first: 100)`` is not a guess about how many runs exist: the API
# returns them newest first, and only the newest finished run of each name is
# ever cited, so a hundred is a ceiling on history rather than on coverage.
_PROJECT_QUERY = """
query($entity: String!, $project: String!) {
  project(name: $project, entityName: $entity) {
    name
    entityName
    access
    runCount
    runs(first: 100) {
      edges {
        node { name displayName createdAt state summaryMetrics }
      }
    }
  }
}
"""


# What the project's ``access`` field means, established by comparison rather
# than by reading documentation: four known-public projects — wandb/gallery,
# stacey/estuary, borisd13/dalle-mini, wandb/huggingface — all report
# ``USER_READ``. ``USER_WRITE`` is the "Open" privacy setting, which is
# strictly more permissive: it also lets any signed-in user submit runs into
# the project. That is worth surfacing rather than swallowing, because the
# whole point of citing a hosted run is that a stranger cannot write to it.
_ACCESS_NOTES = {
    "USER_READ": "public — anyone can view it, nobody else can write to it",
    "USER_WRITE": (
        "open — anyone can view it, and anyone signed in to Weights & Biases "
        "can also submit runs to it"
    ),
    "PRIVATE": "private — an anonymous read should not have succeeded",
}
_PUBLIC_WRITE_ACCESS = frozenset({"USER_WRITE"})


class ProjectNotPublicError(RuntimeError):
    """The project could not be read without credentials."""


def describe_access(access: str | None) -> str:
    """Plain-English reading of the project's access level."""
    if access in _ACCESS_NOTES:
        return _ACCESS_NOTES[access]
    # An unrecognised level is reported, never guessed at.
    return f"{access!r} — unrecognised access level, reported as the API returned it"


def accepts_public_writes(access: str | None) -> bool:
    """Can a stranger add runs to this project?

    Conservative on an unknown value: this drives a warning, and inventing a
    warning from a level nobody has seen would be noise.
    """
    return access in _PUBLIC_WRITE_ACCESS


@dataclass(frozen=True)
class LocalReport:
    """One report on disk and the hosted run name that should mirror it."""

    display_name: str
    path: str
    payload: Mapping[str, Any]


def project_url(entity: str, project: str) -> str:
    return f"https://wandb.ai/{entity}/{project}"


def _post_json(url: str, body: Mapping[str, Any], headers: Mapping[str, str]) -> Any:
    request = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), headers=dict(headers)
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_public_project(
    entity: str = DEFAULT_ENTITY,
    project: str = DEFAULT_PROJECT,
    *,
    fetch: Callable[[str, Mapping[str, Any], Mapping[str, str]], Any] = _post_json,
) -> dict[str, Any]:
    """Read a project anonymously. Raises if an anonymous caller cannot see it.

    ``fetch`` is injected so the tests exercise every branch without a
    network call or an account — the same reason the tracker module takes an
    injectable ``wandb``.
    """
    payload = fetch(
        WANDB_GRAPHQL_URL,
        {
            "query": _PROJECT_QUERY,
            "variables": {"entity": entity, "project": project},
        },
        # Deliberately no Authorization header: see the module docstring.
        {"Content-Type": "application/json"},
    )

    errors = payload.get("errors") if isinstance(payload, Mapping) else None
    if errors:
        messages = "; ".join(str(error.get("message", error)) for error in errors)
        raise ProjectNotPublicError(f"{project_url(entity, project)}: {messages}")

    data = (payload or {}).get("data") or {}
    node = data.get("project")
    if node is None:
        raise ProjectNotPublicError(
            f"{project_url(entity, project)} is not readable without credentials — "
            "either it is private or the entity/project name is wrong"
        )

    edges = ((node.get("runs") or {}).get("edges")) or []
    return {
        "entity": node.get("entityName", entity),
        "project": node.get("name", project),
        "access": node.get("access"),
        "run_count": node.get("runCount"),
        "runs": [edge["node"] for edge in edges if edge.get("node")],
    }


def latest_finished_runs(runs: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """The newest *finished* run for each run name, with its summary parsed.

    A crashed run's summary is a partial write, not a result, so it never
    becomes the run a document cites.
    """
    latest: dict[str, dict[str, Any]] = {}
    for run in runs:
        if run.get("state") != "finished":
            continue
        try:
            summary = json.loads(run.get("summaryMetrics") or "")
        except (TypeError, ValueError):
            continue
        if not isinstance(summary, Mapping):
            continue

        name = run.get("displayName") or run.get("name")
        current = latest.get(name)
        # ISO-8601 UTC timestamps sort lexicographically, so this needs no
        # date parsing — and a malformed timestamp loses rather than throws.
        if current is None or str(run.get("createdAt")) > str(current.get("createdAt")):
            latest[name] = {**run, "summary": dict(summary)}
    return latest


def compare_run(
    hosted_summary: Mapping[str, Any],
    local_report: Mapping[str, Any],
    *,
    tolerance: float = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """Compare one hosted run's summary against one report on disk."""
    # ``_step``/``_runtime``/``_timestamp``/``_wandb`` are the tracker's own
    # bookkeeping, not measurements of this system. Booleans are excluded for
    # the same reason ``flatten_metrics`` excludes them: Python treats them as
    # ints, and a schema flag is not a measurement.
    hosted = {
        key: value
        for key, value in hosted_summary.items()
        if not key.startswith("_")
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
    }
    local = flatten_metrics(local_report)

    shared = sorted(set(hosted) & set(local))
    mismatched = [
        {"metric": key, "hosted": hosted[key], "local": local[key]}
        for key in shared
        if abs(float(hosted[key]) - float(local[key])) > tolerance
    ]
    missing_from_hosted = sorted(set(local) - set(hosted))
    only_in_hosted = sorted(set(hosted) - set(local))

    return {
        "compared": len(shared),
        "matched": len(shared) - len(mismatched),
        "mismatched": mismatched,
        "missing_from_hosted": missing_from_hosted,
        "only_in_hosted": only_in_hosted,
        # Zero shared metrics is not evidence of anything, so it cannot pass.
        "ok": bool(shared) and not mismatched and not missing_from_hosted and not only_in_hosted,
    }


def verify_runs(
    runs: Iterable[Mapping[str, Any]],
    reports: Sequence[LocalReport],
    *,
    entity: str = DEFAULT_ENTITY,
    project: str = DEFAULT_PROJECT,
    tolerance: float = DEFAULT_TOLERANCE,
    access: str | None = None,
) -> dict[str, Any]:
    """Check every report against its hosted run and summarise the verdict."""
    latest = latest_finished_runs(runs)
    entries: list[dict[str, Any]] = []

    for report in reports:
        run = latest.get(report.display_name)
        if run is None:
            entries.append(
                {
                    "display_name": report.display_name,
                    "report": report.path,
                    "ok": False,
                    "reason": f"no finished run named {report.display_name!r} on the server",
                    "compared": 0,
                    "matched": 0,
                }
            )
            continue

        comparison = compare_run(run["summary"], report.payload, tolerance=tolerance)
        entries.append(
            {
                "display_name": report.display_name,
                "report": report.path,
                "run_id": run.get("name"),
                "run_url": f"{project_url(entity, project)}/runs/{run.get('name')}",
                "created_at": run.get("createdAt"),
                **comparison,
            }
        )

    return {
        "entity": entity,
        "project": project,
        "project_url": project_url(entity, project),
        "fetched_anonymously": True,
        "access": access,
        "access_note": describe_access(access),
        # Not a failure: an over-open project still reproduces its reports.
        # It is a warning, because a project a stranger can write to is
        # weaker evidence than one they cannot.
        "accepts_public_writes": accepts_public_writes(access),
        "tolerance": tolerance,
        "metrics_compared": sum(entry["compared"] for entry in entries),
        "metrics_matched": sum(entry["matched"] for entry in entries),
        "verified": bool(entries) and all(entry["ok"] for entry in entries),
        "runs": entries,
    }
