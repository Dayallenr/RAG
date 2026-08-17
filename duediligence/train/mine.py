"""
Turn synthetic queries into training triplets with hard negatives.

**Why hard negatives at all.** Contrastive fine-tuning learns from what it
must push *apart*, not only what it must pull together. Random negatives are
trivially separable — a question about Columbia's deposits versus a passage
about a different bank's board committees teaches almost nothing. Negatives
mined from the retriever's own top results are the passages it currently
confuses with the right answer, which is exactly where the headroom is.

**Company names are normalised first, and this fixes a flaw in the generated
data.** The generation prompt passed the ticker as metadata and asked the
model to name the company explicitly, so it wrote questions about "Colb" and
"Wsbc". No real user asks about "Colb". Training on those would spend model
capacity associating a token that never appears in a genuine query. The
substitution is deterministic and applied here rather than by regenerating
4,776 queries.

**Splitting happens by query, never by row.** One query yields several
triplets; letting those land on both sides of the split would leak the
validation set into training and make early stopping meaningless.

**Negatives are excluded by content, not only by chunk id.** Chunk ids are
not purely content-addressed, so the same boilerplate paragraph recurring
across filings — "Holders of our common stock are only entitled to receive
such dividends as our board of directors declares..." — exists under several
ids. Excluding the positive by id alone let its byte-identical twin back in
as a "hard negative": 1,069 of 14,292 mined rows, across 505 queries, asked
the loss to score one string as both the positive and the negative for the
same anchor. That is not a hard example, it is an unsatisfiable one — it
contributes a loss floor and contradictory gradients, and nothing about it
raises an error. Selection therefore compares normalised text.
"""
from __future__ import annotations

import logging
import re
from collections.abc import Iterable

logger = logging.getLogger(__name__)

__all__ = [
    "COMPANY_NAMES",
    "normalize_company_names",
    "select_negatives",
    "split_by_query",
    "text_key",
]

_WHITESPACE_RE = re.compile(r"\s+")

# Real names as the filings themselves use them, which is also how a user
# would ask.
COMPANY_NAMES = {
    "COLB": "Columbia Banking System",
    "UMPQ": "Umpqua Holdings",
    "GBCI": "Glacier Bancorp",
    "WSBC": "WesBanco",
    "SSB": "South State",
}

# Matches the ticker however the model cased it — "Colb", "COLB", "colb" —
# as a whole word, so "Colbert" and similar are untouched.
_TICKER_PATTERNS = {
    ticker: re.compile(rf"\b{ticker}\b", re.IGNORECASE) for ticker in COMPANY_NAMES
}


def normalize_company_names(query: str) -> str:
    """Replace ticker-as-company-name with the real company name.

    Applied to every synthetic query. A query already using the real name is
    left alone, since the pattern only matches the ticker itself.
    """
    for ticker, pattern in _TICKER_PATTERNS.items():
        query = pattern.sub(COMPANY_NAMES[ticker], query)
    return query


def text_key(text: str) -> str:
    """Normalised form used to decide whether two chunks say the same thing.

    Case and whitespace only. Anything cleverer (stemming, near-duplicate
    thresholds) would start discarding genuinely distinct passages, and the
    problem this exists to solve is exact repetition of boilerplate.
    """
    return _WHITESPACE_RE.sub(" ", text).strip().casefold()


def select_negatives(
    candidates: list[tuple[str, str]],
    positive_id: str,
    positive_text: str,
    *,
    n: int = 4,
    skip_top: int = 0,
    also_exclude: Iterable[str] = (),
) -> list[str]:
    """Pick hard negatives from what the retriever actually returned.

    ``candidates`` is ``(chunk_id, text)`` in retrieval order; the returned
    ids keep that order.

    The positive is removed rather than assumed absent — it is usually in
    there, and training a model to push a passage away from a query it
    correctly answers would be actively harmful. It is removed **by id and
    by normalised text**: ids are not purely content-addressed, so the same
    boilerplate paragraph appears under several of them, and an id-only
    check readmits the positive's own twin as a negative (see the module
    docstring).

    Negatives are also deduplicated against each other on the same key. Two
    byte-identical negatives for one anchor spend two of ``n`` slots on one
    example, and under an in-batch loss they contradict each other exactly
    as a duplicated positive would.

    ``also_exclude`` holds further passage texts this query is known to be
    answered by. A generic question ("What regulatory constraints does the
    Company face?") gets generated from more than one filing, so a passage
    that is a *positive* for one copy of the query would otherwise be mined
    as a negative for another — the same false-negative problem one level up.

    ``skip_top`` optionally drops the highest-ranked surviving hits. The
    corpus contains genuine *near*-duplicates (the same merger described in
    both companies' 8-Ks), so the very top non-positive hit is sometimes a
    passage that answers the question just as well — a false negative this
    exact-match filter cannot catch. This is the knob for trading that risk
    against negative difficulty.
    """
    seen = {key for text in also_exclude if (key := text_key(text))}
    positive_key = text_key(positive_text)
    if positive_key:
        seen.add(positive_key)

    negatives: list[str] = []
    for chunk_id, text in candidates:
        if chunk_id == positive_id:
            continue
        key = text_key(text)
        # An empty chunk teaches nothing and cannot be told apart from any
        # other empty one.
        if not key or key in seen:
            continue
        seen.add(key)
        negatives.append(chunk_id)

    return negatives[skip_top : skip_top + n]


def split_by_query(rows: list[dict], *, val_fraction: float = 0.1, seed: int = 17):
    """Split triplets into train and validation, grouped by query.

    Grouping is the point: one query produces several triplets, and putting
    some in train and others in validation would leak, making the validation
    loss an optimistic measure of memorisation rather than generalisation.
    """
    import random

    queries = sorted({row["query"] for row in rows})
    rng = random.Random(seed)
    rng.shuffle(queries)

    n_val = max(1, int(len(queries) * val_fraction)) if queries else 0
    val_queries = set(queries[:n_val])

    train = [r for r in rows if r["query"] not in val_queries]
    validation = [r for r in rows if r["query"] in val_queries]

    assert not ({r["query"] for r in train} & {r["query"] for r in validation}), (
        "train and validation share a query — the split leaked"
    )
    return train, validation
