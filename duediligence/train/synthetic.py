"""
Synthetic query generation for retrieval fine-tuning.

**Why this exists.** Fine-tuning a bi-encoder needs thousands of
(query, passage) pairs. This project has 101 hand-written questions — far
too few to train on, and, more importantly, they are the exact questions the
headline retrieval numbers are scored against. Training on them would make
the reported "improvement" a measurement of memorisation. So training data
is generated from the corpus instead, in the established doc2query/InPars
style: show a model a passage, ask what questions it answers, keep the pairs.

**The contamination guard is the point of this module, not a detail.** Every
chunk that any eval question is labelled against is excluded from generation,
and any generated query too similar to an eval question is dropped. Both
checks are enforced here and asserted by tests, because "we remembered not
to train on the test set" is not a property anyone can verify later, whereas
a failing test is.

**Stated limitation, which belongs in the README and not only here.**
Synthetic queries are produced by reading the passage, so they inherit the
same lexical-overlap bias as the hand-written eval questions: they share
vocabulary with the text they are derived from, which structurally favours
lexical matching. This does not invalidate a fine-tuning delta measured on
the held-out human set, but it does mean the synthetic data is not a
neutral sample of how a real user would ask.
"""
from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from pathlib import Path

from duediligence.eval.eval_set import load_eval_set

logger = logging.getLogger(__name__)

__all__ = [
    "GENERATION_PROMPT",
    "EvalLeakageError",
    "assert_no_eval_leakage",
    "build_prompt",
    "eval_chunk_ids",
    "eval_question_keys",
    "is_contaminated",
    "normalize_question",
    "parse_questions",
]


class EvalLeakageError(RuntimeError):
    """A held-out eval question reached the training data."""

# Below this many characters a chunk carries too little to ask about — a
# heading, a page number, a one-line "None." item. Generating from them
# produces questions no retriever could reasonably answer.
MIN_CHUNK_CHARS = 200

# Jaccard overlap on normalized word sets, above which a generated query is
# treated as the same question as an eval one. Deliberately cautious: the
# cost of dropping a usable training pair is negligible (there are
# thousands), and the cost of leaking a test question into training is the
# whole result.
CONTAMINATION_THRESHOLD = 0.6

GENERATION_PROMPT = """\
You are creating training data for a search system over SEC filings from US \
regional banks.

Read the passage below and write {n} distinct questions that this passage \
directly answers.

Rules:
1. Each question must be answerable using ONLY this passage.
2. Write questions a financial analyst would actually ask — about figures, \
risks, terms, dates, or events.
3. Name the company or the subject explicitly. Do not write "this bank" or \
"the company", because the question will be searched against a corpus of \
five different banks.
4. Do not reference "the passage" or "the document" in the question itself.
5. Vary the phrasing. Do not copy long word-for-word spans from the passage.
6. Output ONLY the questions, one per line, with no numbering and no \
commentary.

--- PASSAGE ({company} {filing_type} filed {filing_date}) ---
{text}

--- QUESTIONS ---
"""

_WORD_RE = re.compile(r"[a-z0-9]+")
_LEADING_ENUMERATION_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*")


def normalize_question(question: str) -> frozenset[str]:
    """Reduce a question to its word set for overlap comparison."""
    return frozenset(_WORD_RE.findall(question.lower()))


def _require_eval_set(eval_set_path: str | Path, why: str) -> list[dict]:
    """Load the eval set, or fail loudly saying which guard cannot run.

    A missing eval set must never degrade into "generate anyway with no
    contamination check" — that silently produces training data drawn from
    the test set, and the resulting delta measures memorisation. Parsing is
    delegated so this module reads the same file, the same way, as the
    evaluation that scores against it.
    """
    if not Path(eval_set_path).exists():
        raise FileNotFoundError(f"{eval_set_path} not found — {why}")
    return load_eval_set(str(eval_set_path))


def eval_chunk_ids(eval_set_path: str | Path) -> set[str]:
    """Every chunk id any eval question is labelled against.

    These are the passages the test set is scored on. Generating training
    queries from them would put the test set's own evidence into training,
    which is the contamination this module exists to prevent.
    """
    entries = _require_eval_set(
        eval_set_path,
        "refusing to generate training data without the eval set, because the "
        "contamination guard cannot run without it.",
    )
    ids: set[str] = set()
    for entry in entries:
        ids.update(entry.get("relevant_chunk_ids", []))
    return ids


def eval_question_keys(eval_set_path: str | Path) -> list[frozenset[str]]:
    """Every held-out question, reduced to the form comparisons use."""
    entries = _require_eval_set(
        eval_set_path,
        "refusing to proceed without the eval set, because the contamination "
        "guard cannot run without it.",
    )
    return [normalize_question(entry["question"]) for entry in entries]


def assert_no_eval_leakage(queries: Iterable[str], eval_set_path: str | Path) -> int:
    """Refuse to proceed if any held-out question reached the training data.

    The last line of defence, and the reason it is here rather than inside
    the training script: a contaminated run produces a number that looks
    like an improvement and is not one, and nothing downstream would reveal
    it. That is worth a test, and a script-local function cannot have one.

    Comparison is on normalised word sets, so a question differing only in
    casing, punctuation or spacing is still caught — those are the forms a
    generator actually produces.

    Returns the number of queries cleared, for logging.
    """
    held_out = set(eval_question_keys(eval_set_path))
    seen = [normalize_question(query) for query in queries]
    leaked = held_out & set(seen)
    if leaked:
        raise EvalLeakageError(
            f"{len(leaked)} eval questions appear in the training data. The "
            "reported delta would measure memorisation, not retrieval."
        )
    return len(seen)


def is_contaminated(
    question: str,
    eval_questions: list[frozenset[str]],
    *,
    threshold: float = CONTAMINATION_THRESHOLD,
) -> bool:
    """Is this generated query too close to a held-out eval question?"""
    words = normalize_question(question)
    if not words:
        return True
    for other in eval_questions:
        if not other:
            continue
        overlap = len(words & other) / len(words | other)
        if overlap >= threshold:
            return True
    return False


def build_prompt(chunk: dict, *, n: int = 3) -> str:
    return GENERATION_PROMPT.format(
        n=n,
        company=chunk.get("company", "?"),
        filing_type=chunk.get("filing_type", "?"),
        filing_date=chunk.get("filing_date", "?"),
        text=chunk.get("text", "").strip(),
    )


def parse_questions(raw: str, *, max_questions: int = 3) -> list[str]:
    """Pull questions out of a model's reply.

    Models ignore "no numbering" often enough that stripping enumeration is
    cheaper than discarding the response. Lines that are not questions are
    dropped rather than repaired — a declarative sentence in a query field
    would train the model on the wrong thing.
    """
    questions = []
    for line in raw.splitlines():
        cleaned = _LEADING_ENUMERATION_RE.sub("", line).strip().strip('"')
        if not cleaned.endswith("?") or len(cleaned) < 15:
            continue
        if cleaned.lower().startswith(("here are", "sure", "questions:")):
            continue
        if cleaned not in questions:
            questions.append(cleaned)
    return questions[:max_questions]
