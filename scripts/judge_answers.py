"""
Judge already-generated answers for groundedness, using a different model
from the one that wrote them.

Generation happened on the GPU machine with a local model. Judging happens
here, with the hosted model, and that separation is the point: a model
grading its own output shares a failure mode, because a claim both find
plausible gets marked supported. The report records which model did which,
and whether they were actually different.

**Quota-bound, so this is resumable and subset-based.** The hosted free tier
allows a verified 20 requests/day. 68 non-refused answers therefore take
several days at full coverage, which is why ``--limit`` defaults to a day's
worth and completed judgments are skipped on re-run. Judging a stratified
subset and saying so is more honest than judging everything slowly and
reporting a number nobody waited for.

Refusals are not judged. "The provided filings do not state this" makes no
factual claim, so there is nothing to check for support — and counting it as
fully supported would inflate the score with answers that asserted nothing.

    python scripts/judge_answers.py --limit 20      # one day's quota
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.config import load_config  # noqa: E402
from duediligence.eval.run_groundedness_eval import (  # noqa: E402
    describe_judging,
    guard_judgment_regression,
    judge_groundedness,
    summarize,
)
from duediligence.generate.backends import GeminiBackend  # noqa: E402
from duediligence.generate.ollama_backend import OllamaBackend  # noqa: E402
from duediligence.track import flatten_metrics, log_run  # noqa: E402

logger = logging.getLogger("judge")


# A 503 is the hosted model shedding load and costs no quota, so retrying is
# free and usually works. A 429 is the daily allowance actually gone, and
# retrying that just wastes wall-clock on a request that cannot succeed until
# tomorrow. Treating both the same is what made a single transient blip end a
# whole judging run.
_TRANSIENT_MARKERS = ("503", "UNAVAILABLE", "500", "INTERNAL", "deadline", "timeout")
_QUOTA_MARKERS = ("429", "RESOURCE_EXHAUSTED", "quota")


def is_transient(error: Exception) -> bool:
    text = str(error)
    if any(marker in text for marker in _QUOTA_MARKERS):
        return False
    return any(marker in text for marker in _TRANSIENT_MARKERS)


def judge_with_retry(answer, passages, *, backend, attempts: int = 4):
    """Judge one answer, retrying transient failures with backoff.

    Raises on quota exhaustion so the caller stops cleanly rather than
    hammering an endpoint that will refuse until the allowance resets.
    """
    delay = 5.0
    for attempt in range(1, attempts + 1):
        try:
            return judge_groundedness(answer, passages, backend=backend)
        except Exception as error:  # noqa: BLE001 - classified immediately below
            if not is_transient(error) or attempt == attempts:
                raise
            logger.warning(
                "transient failure (attempt %d/%d), retrying in %.0fs: %s",
                attempt, attempts, delay, str(error)[:120],
            )
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("unreachable")


def _load(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def stratified(rows: list[dict], n: int, *, seed: int = 7) -> list[dict]:
    """Spread the judged subset across companies and answer shapes rather
    than taking the first N, which would over-sample whichever company the
    eval set happens to list first."""
    if n >= len(rows):
        return rows
    buckets: dict[tuple, list[dict]] = {}
    for row in rows:
        key = (row.get("company"), bool(row.get("citations")))
        buckets.setdefault(key, []).append(row)
    rng = random.Random(seed)
    for bucket in buckets.values():
        rng.shuffle(bucket)

    picked: list[dict] = []
    while len(picked) < n:
        progressed = False
        for bucket in buckets.values():
            if bucket and len(picked) < n:
                picked.append(bucket.pop())
                progressed = True
        if not progressed:
            break
    return picked


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answers", default="results/generation/answers.jsonl")
    parser.add_argument("--contexts", default="data/generation/retrieval_contexts.jsonl")
    parser.add_argument("--judgments", default="results/generation/judgments.jsonl")
    parser.add_argument("--out", default="results/generation/report.json")
    parser.add_argument("--limit", type=int, default=20, help="max judge calls (daily quota)")
    parser.add_argument("--report-only", action="store_true", help="rebuild the report, judge nothing")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    config = load_config()
    answers = _load(args.answers)
    passages_by_id = {r["eval_id"]: r["passages"] for r in _load(args.contexts)}
    judgments = {r["eval_id"]: r["judge"] for r in _load(args.judgments)}

    # The generator is recorded from the data rather than assumed — the
    # answers say which model wrote them. Taking the *first* labelled row and
    # applying it to the whole file is only sound while the file has one
    # generator, so that is checked rather than hoped for: a mixed file would
    # otherwise let an answer written by the judge itself be reported as
    # independently judged, which is the one claim this report exists to make.
    generators = sorted({r["generated_by"] for r in answers if r.get("generated_by")})
    if len(generators) > 1:
        raise SystemExit(
            f"{args.answers} has answers from more than one generator "
            f"({', '.join(generators)}), so a single independence verdict "
            "cannot describe them. Judge each generator's answers into its "
            "own report, or regenerate the file with one model."
        )
    generator_model = generators[0] if generators else "unknown"
    generation_backend = OllamaBackend(generator_model)
    judge_backend = GeminiBackend(config.models.generation_model)

    if not args.report_only:
        candidates = [
            r for r in answers
            if r["route"] == "semantic" and not r.get("refused")
            and r["eval_id"] not in judgments
        ]
        pending = stratified(candidates, args.limit)
        logger.info(
            "%d judged already, %d eligible, judging %d this run",
            len(judgments), len(candidates), len(pending),
        )

        judgments_path = Path(args.judgments)
        judgments_path.parent.mkdir(parents=True, exist_ok=True)
        with judgments_path.open("a") as handle:
            for index, row in enumerate(pending, start=1):
                try:
                    verdict = judge_with_retry(
                        row["answer"], passages_by_id.get(row["eval_id"], []),
                        backend=judge_backend,
                    )
                except Exception as error:  # noqa: BLE001 - stop cleanly, keep what is done
                    reason = "daily quota exhausted" if not is_transient(error) else "repeated failures"
                    logger.error("stopping at %s (%s): %s", row["eval_id"], reason, str(error)[:160])
                    break
                handle.write(json.dumps({"eval_id": row["eval_id"], "judge": verdict}) + "\n")
                handle.flush()
                judgments[row["eval_id"]] = verdict
                logger.info("judged %s (%d/%d)", row["eval_id"], index, len(pending))
                time.sleep(2)

    merged = [dict(r, judge=judgments[r["eval_id"]]) if r["eval_id"] in judgments else r
              for r in answers]

    report = summarize(merged, total_questions=len(answers))
    report["judging"] = describe_judging(
        generation_backend=generation_backend, judge_backend=judge_backend
    )
    report["judged_subset"] = {
        "judged": len(judgments),
        "eligible": sum(1 for r in answers if r["route"] == "semantic" and not r.get("refused")),
        "note": (
            "A stratified subset, not the full set: the hosted judge is capped at "
            "20 requests/day. Refusals are excluded from judging because they make "
            "no factual claim to support."
        ),
    }

    output = Path(args.out)
    # Same protection the module-level entry point gets. This script is the
    # recommended writer of this file, and it regresses it just as silently
    # when --judgments points somewhere empty or the verdicts are lost.
    guard_judgment_regression(report, output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")

    judging = report["judging"]
    print(f"\nanswers: {report['answers_generated']}/{report['questions_in_eval_set']}")
    print(f"  structured {report['structured_route']}   semantic {report['semantic_route']}"
          f"   refusals {report['refusals']}")
    print(f"  valid citations: {report['answers_with_valid_citations']}"
          + (f" ({report['citation_coverage']:.0%})" if report["citation_coverage"] is not None else ""))
    print(f"\n  generated by {judging['generation']['model']}"
          f"   judged by {judging['judge']['model']}"
          f"   independent: {judging['independent_judge']}")
    print(f"  judged {report['judged_subset']['judged']}/{report['judged_subset']['eligible']} eligible")
    if report["mean_claim_support_rate"] is not None:
        print(f"  mean claim support: {report['mean_claim_support_rate']:.1%}")
        print(f"  fully supported: {report['fully_supported_answers']}/{report['judged_answers']}")

    url = log_run(
        name="groundedness-eval", tags=["generation", "eval"],
        config={
            "generation_model": judging["generation"]["model"],
            "judge_model": judging["judge"]["model"],
            "independent_judge": judging["independent_judge"],
            "judged": report["judged_subset"]["judged"],
        },
        metrics=flatten_metrics(report),
    )
    if url:
        print(f"\ntracked: {url}")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
