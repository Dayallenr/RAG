"""
Groundedness eval: is every claim in a generated answer actually supported
by the passages it was given?

This measures the failure mode that matters most for a due-diligence tool.
A retrieval miss is visible — the user reads the passages and sees they are
off-topic. An ungrounded *answer* is invisible: it is fluent, it carries
citation markers, and the figure in it is wrong. That is the one outcome
that would make this system worse than useless to someone doing real
diligence.

Three things are checked, and only one of them needs a model:

* **Citation validity** (free, deterministic). Every `[n]` the model emits
  must resolve to a passage that was actually supplied. Out-of-range
  citations are fabricated provenance. Computed by ``parse_citations``.
* **Citation coverage** (free, deterministic). Did the answer cite anything
  at all, or assert facts with no source?
* **Claim support** (one Gemini call per answer). An LLM-as-judge pass
  asking whether each claim is entailed by the cited passages. This is the
  expensive part and the least trustworthy — see the caveat below.

**Quota discipline: this script is resumable and must stay that way.** The
verified free-tier limit on this key is 20 requests/day for the flash model
(CLAUDE.md), and a full pass over the eval set needs one generation call per
question plus one judging call. Completed questions are keyed by
``eval_id`` in the output file and skipped on re-run, the same pattern
``scripts/run_chart_extraction.py`` uses. Re-running after a 429 resumes
rather than restarting, so a day's quota is never spent redoing finished
work. ``--limit`` bounds a single session's spend.

**The judge caveat, stated plainly.** Using Gemini to grade Gemini's own
output shares a failure mode: a claim both models find plausible gets
marked supported. The deterministic citation checks do not have that
problem, which is why they are reported separately rather than folded into
one score. Treat claim-support as indicative; treat citation validity as
measured.
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

from duediligence.config import load_config
from duediligence.generate.backends import (
    GeminiBackend,
    TextGenerationBackend,
    backends_are_independent,
)

logger = logging.getLogger(__name__)

__all__ = ["describe_judging", "judge_groundedness", "run_groundedness_eval"]

_JUDGE_PROMPT = """\
You are grading whether an ANSWER is fully supported by the PASSAGES it was \
given. Do not use outside knowledge — a claim is supported only if these \
passages state it.

Reply with strict JSON and nothing else:
{{"total_claims": <int>, "supported_claims": <int>, "unsupported": [<string>, ...]}}

where "unsupported" lists any factual claim in the answer that the passages \
do not support (empty list if all are supported).

--- PASSAGES ---
{passages}

--- ANSWER ---
{answer}
"""


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def describe_judging(
    *,
    generation_backend: TextGenerationBackend,
    judge_backend: TextGenerationBackend,
) -> dict:
    """Provenance for the report: who wrote the answers, who graded them, and
    whether those were actually different models.

    Recorded rather than assumed. A support rate produced by a model grading
    its own output is a materially weaker number than one from an independent
    judge, and a reader cannot tell the two apart from the score alone.
    """
    return {
        "generation": generation_backend.describe(),
        "judge": judge_backend.describe(),
        "independent_judge": backends_are_independent(generation_backend, judge_backend),
    }


def judge_groundedness(answer: str, passages: list[dict], *, backend) -> dict:
    """One LLM-as-judge call. Returns parsed verdict or an error marker."""
    rendered = "\n\n".join(
        f"[{i}] {p.get('text', '')}" for i, p in enumerate(passages, start=1)
    )
    raw = backend.generate(_JUDGE_PROMPT.format(passages=rendered, answer=answer))

    # Models wrap JSON in markdown fences often enough that stripping them
    # is worth doing rather than counting it as a judging failure.
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        raw = raw[4:] if raw.startswith("json") else raw
    try:
        verdict = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("judge returned unparseable output: %s", raw[:200])
        return {"judge_error": "unparseable", "raw": raw[:500]}

    total = int(verdict.get("total_claims", 0) or 0)
    supported = int(verdict.get("supported_claims", 0) or 0)
    return {
        "total_claims": total,
        "supported_claims": supported,
        "support_rate": supported / total if total else None,
        "unsupported": verdict.get("unsupported", []),
    }


def run_groundedness_eval(
    eval_set_path: str = "data/eval_set.jsonl",
    output_path: str = "results/generation/answers.jsonl",
    *,
    limit: int | None = None,
    judge: bool = True,
    generation_backend: TextGenerationBackend | None = None,
    judge_backend: TextGenerationBackend | None = None,
    pipeline=None,
) -> dict:
    config = load_config()

    # Both default to the hosted model, which is what this did before the
    # backend seam existed — and which means the default run is *not* an
    # independent judge. The report says so rather than hiding it.
    generation_backend = generation_backend or GeminiBackend(config.models.generation_model)
    judge_backend = judge_backend or GeminiBackend(config.models.generation_model)

    entries = [
        json.loads(line)
        for line in Path(eval_set_path).read_text().splitlines()
        if line.strip()
    ]

    answers_path = Path(output_path)
    answers_path.parent.mkdir(parents=True, exist_ok=True)
    completed = _load_jsonl(answers_path)
    done_ids = {row["eval_id"] for row in completed}
    logger.info("resuming: %d answers already generated, skipping them", len(done_ids))

    pending = [e for e in entries if e["eval_id"] not in done_ids]
    if limit is not None:
        pending = pending[:limit]

    if pending:
        if pipeline is None:
            from duediligence.pipeline import DueDiligencePipeline

            pipeline = DueDiligencePipeline(config, generation_backend=generation_backend)

        with answers_path.open("a") as handle:
            for entry in pending:
                try:
                    result = pipeline.answer(entry["question"])
                    row = {
                        "eval_id": entry["eval_id"],
                        "question": entry["question"],
                        "route": result["route"],
                        "answer": result["answer"],
                        "refused": result["refused"],
                        "citations": result["citations"],
                        "n_passages": len(result["passages"]),
                        "passage_chunk_ids": [p["chunk_id"] for p in result["passages"]],
                    }
                    if judge and result["route"] == "semantic" and not result["refused"]:
                        row["judge"] = judge_groundedness(
                            result["answer"], result["passages"], backend=judge_backend,
                        )
                    # Written immediately, one line at a time — a 429 on the
                    # next question must not lose the work already paid for.
                    handle.write(json.dumps(row) + "\n")
                    handle.flush()
                    logger.info("answered %s (route=%s)", entry["eval_id"], result["route"])
                    time.sleep(1)  # gentle on the per-minute limit
                except Exception as error:  # noqa: BLE001 - quota errors must not lose progress
                    logger.error("stopping at %s: %s", entry["eval_id"], error)
                    break

    report = summarize(_load_jsonl(answers_path), total_questions=len(entries))
    report["judging"] = describe_judging(
        generation_backend=generation_backend, judge_backend=judge_backend
    )
    return report


def summarize(rows: list[dict], *, total_questions: int) -> dict:
    semantic = [r for r in rows if r.get("route") == "semantic"]
    answered = [r for r in semantic if not r.get("refused")]
    judged = [r for r in answered if isinstance(r.get("judge"), dict) and "support_rate" in r["judge"]]

    with_citations = sum(1 for r in answered if r.get("citations"))
    support_rates = [r["judge"]["support_rate"] for r in judged if r["judge"]["support_rate"] is not None]

    return {
        "questions_in_eval_set": total_questions,
        "answers_generated": len(rows),
        "coverage": len(rows) / total_questions if total_questions else 0.0,
        "structured_route": sum(1 for r in rows if r.get("route") == "structured"),
        "semantic_route": len(semantic),
        "refusals": sum(1 for r in semantic if r.get("refused")),
        "refusal_rate": (
            sum(1 for r in semantic if r.get("refused")) / len(semantic) if semantic else None
        ),
        # Deterministic, fully trustworthy: parse_citations already dropped
        # any citation that did not resolve to a supplied passage, so every
        # citation counted here provably points at a real indexed chunk.
        "answers_with_valid_citations": with_citations,
        "citation_coverage": with_citations / len(answered) if answered else None,
        # LLM-as-judge; see the module docstring's caveat.
        "judged_answers": len(judged),
        "mean_claim_support_rate": (
            sum(support_rates) / len(support_rates) if support_rates else None
        ),
        "fully_supported_answers": sum(1 for r in support_rates if r == 1.0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", default="data/eval_set.jsonl")
    parser.add_argument("--answers", default="results/generation/answers.jsonl")
    parser.add_argument("--out", default="results/generation/report.json")
    parser.add_argument(
        "--limit", type=int, default=None,
        help="max NEW questions this session (guards the 20/day Gemini quota)",
    )
    parser.add_argument("--no-judge", action="store_true", help="skip the LLM-as-judge call")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("opensearch").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    report = run_groundedness_eval(
        args.eval_set, args.answers, limit=args.limit, judge=not args.no_judge
    )

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")

    print(f"\nanswers generated: {report['answers_generated']}/{report['questions_in_eval_set']} "
          f"({report['coverage']:.0%} of the eval set)")
    print(f"  routed structured: {report['structured_route']}   semantic: {report['semantic_route']}")
    print(f"  refusals: {report['refusals']}"
          + (f" ({report['refusal_rate']:.0%} of semantic answers)" if report["refusal_rate"] is not None else ""))
    print(f"  answers with valid citations: {report['answers_with_valid_citations']}"
          + (f" ({report['citation_coverage']:.0%})" if report["citation_coverage"] is not None else ""))
    judging = report["judging"]
    print(f"  generated by: {judging['generation']['model']}"
          f"   judged by: {judging['judge']['model']}")
    if report["mean_claim_support_rate"] is not None:
        print(f"  mean claim support (LLM judge, {report['judged_answers']} judged): "
              f"{report['mean_claim_support_rate']:.1%}")
        print(f"  fully supported answers: {report['fully_supported_answers']}/{report['judged_answers']}")
        if not judging["independent_judge"]:
            # Stated at the point the number is printed, not only in a
            # docstring — a self-graded support rate looks identical to an
            # independently judged one unless something says otherwise.
            print("  NOTE: judged by the same model that generated the answers — "
                  "treat claim support as indicative, not measured.")
    else:
        print("  no judged answers yet")

    if report["coverage"] < 1.0:
        print(
            f"\nPartial run — {report['questions_in_eval_set'] - report['answers_generated']} "
            "questions remain. Re-run tomorrow to continue; completed answers are skipped "
            "(20 Gemini requests/day free-tier limit)."
        )
    print(f"\nwrote {output}")


if __name__ == "__main__":
    main()
