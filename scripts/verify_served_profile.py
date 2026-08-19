"""Serve each profile through the real API and check what comes back.

#24 asks for one thing that cannot be asserted from a config file: that
setting an environment variable makes the *running service* answer with the
fine-tuned model and its index, with no rebuilt image and no code change.
This runs the actual FastAPI app — real lifespan, real pipeline, real
models, real OpenSearch — once per profile, and records what each arm
reported and returned.

Three things are checked per arm, because each fails differently:

1. **Identity.** ``/healthz`` and ``/readyz`` must name the model that was
   loaded and the index it is paired with. A container holding a model that
   does not match its index returns plausible answers built on cosine
   similarity across two incompatible vector spaces — no error anywhere in
   the request path. The endpoints reporting the pair is the only way that
   becomes observable from outside the process.

2. **Retrieval.** ``/search`` must return hits. An arm that reports the
   right index and then returns nothing has not demonstrated serving.

3. **Divergence.** The two arms must not be the same run wearing two
   labels. Compared with reranking off, where the bi-encoder's ranking
   survives: the fused order must differ, or the profile switch did
   nothing.

And one thing is checked *across* the arms and expected to show no change:
with reranking on — the served default — #23 measured the fine-tune's
effect through the cross-encoder at +0.000 on every metric, because at
dense weight 0.25 and candidate depth 50 the fused pool *is* BM25's
candidate set, so the bi-encoder reorders a pool whose membership it never
changes and the reranker discards that order. Identical reranked lists here
are therefore the *expected* result and are recorded as such. Serving this
profile is a measured no-op for users; this script is what makes that
statement a measurement rather than a claim.

Usage:
    python scripts/verify_served_profile.py
    python scripts/verify_served_profile.py --profile finetuned --k 5
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.config import PROFILE_ENV_VAR, load_config  # noqa: E402

logger = logging.getLogger("verify_served_profile")

DEFAULT_QUERIES = [
    "What are the risks of the merger with Umpqua?",
    "How did Columbia account for credit losses in 2023?",
    "What is the date of the merger agreement between Columbia and Umpqua?",
]


@contextmanager
def profile_env(profile: str | None):
    """Set (or clear) the profile variable for the duration of one arm.

    The variable is what a deployment actually sets, so the arms are driven
    through it rather than through ``load_config(profile=...)``: passing the
    argument would test a code path no container uses.
    """
    previous = os.environ.pop(PROFILE_ENV_VAR, None)
    if profile:
        os.environ[PROFILE_ENV_VAR] = profile
    try:
        yield
    finally:
        os.environ.pop(PROFILE_ENV_VAR, None)
        if previous is not None:
            os.environ[PROFILE_ENV_VAR] = previous


def identity_problems(
    *, expected_profile: str | None, expected_model: str, expected_index: str, reported: dict
) -> list[str]:
    """Every way the service's self-report disagrees with the profile asked for.

    Named individually rather than returned as one boolean: "the model is
    right but the index is not" is the mismatched pair this endpoint exists
    to expose, and collapsing it into a pass/fail would hide which half moved.
    """
    problems = []
    if reported.get("profile") != expected_profile:
        problems.append(
            f"reported profile {reported.get('profile')!r}, expected {expected_profile!r}"
        )
    if reported.get("model") != expected_model:
        problems.append(f"reported model {reported.get('model')!r}, expected {expected_model!r}")
    if reported.get("index") != expected_index:
        problems.append(f"reported index {reported.get('index')!r}, expected {expected_index!r}")
    return problems


def divergence(base: list[str], candidate: list[str]) -> dict[str, Any]:
    """How two ranked lists of chunk ids differ, as sets and as order."""
    return {
        "same_members": sorted(base) == sorted(candidate),
        "same_order": base == candidate,
        "only_in_base": [i for i in base if i not in candidate],
        "only_in_candidate": [i for i in candidate if i not in base],
    }


def run_arm(profile: str | None, queries: list[str], k: int, fused_k: int) -> dict[str, Any]:
    """Stand the real app up under one profile and record what it reports.

    Returns a report even when the arm fails. The likeliest failure here is
    an operator running the fine-tuned arm on a machine that has neither the
    index nor the checkpoint, which ``/readyz`` answers with a 503 — and a
    traceback with no artifact written is the least useful possible way to
    say so.
    """
    from fastapi.testclient import TestClient

    from duediligence.api.app import create_app

    name = profile or "base"
    with profile_env(profile):
        config = load_config()
        expected_model = config.models.embedding_model
        expected_index = config.opensearch.index_name
        arm: dict[str, Any] = {
            "profile": profile,
            "expected_model": expected_model,
            "expected_index": expected_index,
            "healthz": None,
            "readyz": None,
            "identity_problems": [],
            "rerank_enabled": None,
            "reranked": {},
            "fused_no_rerank": {},
            "empty_results": [],
            "failure": None,
        }

        logger.info("arm %s: loading %s against %s", name, expected_model, expected_index)
        app = create_app()
        try:
            # The context manager is what runs the lifespan, which is what
            # constructs the pipeline — the models really load here.
            with TestClient(app) as client:
                healthz = client.get("/healthz")
                healthz.raise_for_status()
                arm["healthz"] = healthz.json()

                readyz = client.get("/readyz")
                if readyz.status_code != 200:
                    raise RuntimeError(f"/readyz returned {readyz.status_code}: {readyz.text}")
                arm["readyz"] = readyz.json()
                arm["identity_problems"] = identity_problems(
                    expected_profile=profile,
                    expected_model=expected_model,
                    expected_index=expected_index,
                    reported=readyz.json(),
                )

                pipeline = app.state.pipeline
                # ENABLE_RERANK=false is a supported deployment setting and CI
                # sets it. Under it both loops below measure the same fused
                # path, the arms come out *differing* where #23 measured them
                # identical, and every check here still passes — an artifact
                # that contradicts a recorded measurement while looking green.
                arm["rerank_enabled"] = pipeline.reranker is not None
                if pipeline.reranker is None:
                    raise RuntimeError(
                        "the pipeline loaded without a reranker (ENABLE_RERANK is off), "
                        "so the reranked arm would silently measure the fused path"
                    )

                for query in queries:
                    response = client.post("/search", json={"query": query, "k": k})
                    response.raise_for_status()
                    arm["reranked"][query] = [h["chunk_id"] for h in response.json()["results"]]

                # Same loaded models, reranker set aside: the cross-encoder
                # discards the bi-encoder's order, so with it in place the two
                # arms are expected to agree and would prove nothing either way.
                #
                # Taken at candidate depth rather than at k. The fused top-5 is
                # BM25-dominated at dense weight 0.25 — the same arithmetic #23
                # measured — so two genuinely different indexes can agree on
                # the first few ids, and comparing there would report a
                # difference that is not one.
                reranker, pipeline.reranker = pipeline.reranker, None
                try:
                    for query in queries:
                        response = client.post("/search", json={"query": query, "k": fused_k})
                        response.raise_for_status()
                        arm["fused_no_rerank"][query] = [
                            h["chunk_id"] for h in response.json()["results"]
                        ]
                finally:
                    pipeline.reranker = reranker

                arm["empty_results"] = [q for q, hits in arm["reranked"].items() if not hits]
        except Exception as error:  # noqa: BLE001 - recorded, not swallowed
            logger.error("arm %s failed: %s", name, error)
            arm["failure"] = f"{type(error).__name__}: {error}"

    return arm


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="finetuned", help="the profile to serve as the candidate arm")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument(
        "--fused-k",
        type=int,
        default=50,
        help="depth at which the un-reranked orders are compared; the candidate depth the "
        "pipeline itself fuses at, not the k a user sees",
    )
    parser.add_argument("--out", default="results/serving/profile_check.json")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # "base" names the no-profile arm. A profile literally called base would
    # overwrite it, leaving both names pointing at one dict and turning the
    # whole comparison into an index against itself.
    if args.profile == "base":
        parser.error("'base' names the no-profile arm; rename the profile to compare it")

    arms = {
        "base": run_arm(None, DEFAULT_QUERIES, args.k, args.fused_k),
        args.profile: run_arm(args.profile, DEFAULT_QUERIES, args.k, args.fused_k),
    }
    base, candidate = arms["base"], arms[args.profile]

    problems = [
        f"{name} arm failed: {arm['failure']}" for name, arm in arms.items() if arm["failure"]
    ]
    reranked_diff: dict[str, Any] = {}
    fused_diff: dict[str, Any] = {}

    if not problems:
        reranked_diff = {
            query: divergence(base["reranked"][query], candidate["reranked"][query])
            for query in DEFAULT_QUERIES
        }
        fused_diff = {
            query: divergence(base["fused_no_rerank"][query], candidate["fused_no_rerank"][query])
            for query in DEFAULT_QUERIES
        }

        problems += base["identity_problems"] + candidate["identity_problems"]
        problems += [f"no results for {q!r} on the base arm" for q in base["empty_results"]]
        problems += [
            f"no results for {q!r} on the {args.profile} arm" for q in candidate["empty_results"]
        ]
        if base["readyz"]["index"] == candidate["readyz"]["index"]:
            problems.append("both arms served the same index; the profile switch did nothing")
        if all(diff["same_order"] for diff in fused_diff.values()):
            problems.append(
                f"the two arms ranked identically at fused depth {args.fused_k} with reranking "
                "off, so they did not query different vector spaces"
            )

    report = {
        "queries": DEFAULT_QUERIES,
        "k": args.k,
        "fused_k": args.fused_k,
        "arms": arms,
        "reranked_divergence": reranked_diff,
        "fused_divergence": fused_diff,
        # Stated as a finding rather than a problem: #23 measured this and
        # explained it. A reader who sees only "identical" needs to know it
        # was predicted, and a reader who sees it change needs to know that
        # contradicts a recorded measurement.
        "reranked_lists_identical": (
            all(diff["same_order"] for diff in reranked_diff.values()) if reranked_diff else None
        ),
        "problems": problems,
        "passed": not problems,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    logger.info("wrote %s", out)

    for problem in problems:
        logger.error("PROBLEM: %s", problem)
    logger.info(
        "reranked lists identical across arms: %s (expected True — see #23)",
        report["reranked_lists_identical"],
    )
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
