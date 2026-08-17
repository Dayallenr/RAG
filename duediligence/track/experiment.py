"""
Experiment tracking — every eval and ablation run logged somewhere with a
history and a public URL.

Why this exists at all: the reports in ``results/`` are snapshots. They record
what the *current* numbers are, and a re-run overwrites them. That is fine
while the pipeline is fixed and fatal once it is not — fine-tuning produces a
sequence of runs whose whole value is the comparison between them, and a
report file that keeps only the last one throws away the finding. Tracking
keeps the series.

**Tracking never fails a run.** Every entry point here degrades to a no-op:
no API key, package not installed, tracking explicitly switched off — each
returns ``None`` and logs a line. This matters more than it looks. These
scripts do expensive, sometimes rate-limited work (a full re-index, a
20-requests/day judging pass), and losing an hour of that because a
telemetry sidecar could not reach a server would be an absurd trade. The
report file on disk remains the source of truth; tracking is additive.

**Credentials come from the environment, never the repo.** ``WANDB_API_KEY``
is read from the environment or a local ``.env`` (gitignored), the same
pattern ``generate/gemini_client.py`` uses for its key.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["flatten_metrics", "log_run", "tracking_enabled"]

DEFAULT_PROJECT = "duediligence-rag"

# ``per_query`` holds one row per eval question — 101 nested dicts. It belongs
# in the report file, not in a metrics namespace, where it would produce
# thousands of scalar keys and drown the numbers anyone actually plots.
DEFAULT_SKIP = frozenset({"per_query", "ground_truth_caveat", "unsupported"})

# A guard against a future report growing an unexpectedly long list and
# silently generating a metric explosion.
_MAX_LIST_ITEMS = 100

_OFF_VALUES = {"0", "off", "false", "no"}


def tracking_enabled() -> bool:
    """Is tracking both wanted and possible?

    Explicitly switched off wins over a present key, so a developer can run
    the eval locally without polluting the project's run history — which
    otherwise happens every time someone re-runs a script to read its table.
    """
    from dotenv import load_dotenv

    load_dotenv()
    if os.environ.get("DUEDILIGENCE_TRACKING", "").strip().lower() in _OFF_VALUES:
        return False
    return bool(os.environ.get("WANDB_API_KEY"))


def _import_wandb():
    if not tracking_enabled():
        logger.info(
            "experiment tracking off (set WANDB_API_KEY to enable); writing report only"
        )
        return None
    try:
        import wandb
    except ImportError:
        logger.warning("WANDB_API_KEY is set but wandb is not installed — skipping tracking")
        return None
    return wandb


def flatten_metrics(
    payload: Any,
    *,
    prefix: str = "",
    skip: frozenset[str] = DEFAULT_SKIP,
) -> dict[str, float]:
    """Reduce a nested report to the flat scalar metrics a tracker can plot.

    Keys are dotted paths, so ``retrievers.bm25.metrics.recall@10`` stays
    readable and sorts next to its siblings. Lists of dicts — the ablation
    sweeps — are indexed rather than dropped, because the shape of a sweep
    across parameter values is the most interesting thing to plot in the
    whole project.

    Booleans are deliberately excluded. Python treats them as ints, so
    ``verified: true`` would silently become the metric ``verified = 1``,
    which is a fact about the schema masquerading as a measurement.
    """
    flat: dict[str, float] = {}

    if isinstance(payload, dict):
        items = payload.items()
    elif isinstance(payload, list):
        items = [(str(i), v) for i, v in enumerate(payload[:_MAX_LIST_ITEMS])]
    else:
        return flat

    for key, value in items:
        if key in skip:
            continue
        name = f"{prefix}{key}"
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            flat[name] = value
        elif isinstance(value, (dict, list)):
            flat.update(flatten_metrics(value, prefix=f"{name}.", skip=skip))
    return flat


def log_run(
    *,
    name: str,
    config: dict[str, Any],
    metrics: dict[str, float],
    project: str = DEFAULT_PROJECT,
    tags: list[str] | None = None,
    notes: str | None = None,
    wandb_module: Any | None = None,
) -> str | None:
    """Record one run. Returns its URL, or ``None`` when tracking is off.

    ``wandb_module`` is injectable so the tests exercise this without a
    network call or an account — the same reason the generation backend and
    the search client are injectable elsewhere in this project.
    """
    module = wandb_module if wandb_module is not None else _import_wandb()
    if module is None:
        return None

    try:
        run = module.init(
            project=project,
            name=name,
            config=config,
            tags=list(tags or []),
            notes=notes,
            reinit=True,
        )
        try:
            run.log(metrics)
            return getattr(run, "url", None)
        finally:
            run.finish()
    except Exception as error:  # noqa: BLE001 - telemetry must never fail a run
        # A tracking outage must not cost a re-index or a day's model quota.
        logger.warning("experiment tracking failed (%s) — the report file is unaffected", error)
        return None
