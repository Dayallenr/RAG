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
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

__all__ = [
    "COMPANY_NAMES",
    "normalize_company_names",
    "select_negatives",
    "split_by_query",
]

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


def select_negatives(
    retrieved_ids: list[str],
    positive_id: str,
    *,
    n: int = 4,
    skip_top: int = 0,
) -> list[str]:
    """Pick hard negatives from what the retriever actually returned.

    The positive is removed rather than assumed absent — it is usually in
    there, and training a model to push a passage away from a query it
    correctly answers would be actively harmful.

    ``skip_top`` optionally drops the highest-ranked hits. The corpus
    contains genuine near-duplicates (the same merger described in both
    companies' 8-Ks), so the very top non-positive hit is sometimes a
    passage that answers the question just as well — a false negative. This
    is the knob for trading that risk against negative difficulty.
    """
    negatives = [cid for cid in retrieved_ids if cid != positive_id]
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
