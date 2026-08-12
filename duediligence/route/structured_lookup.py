"""
Exact-value lookup over the extracted XBRL facts.

This is the other half of the routing decision in ``query_router.py``: once
a query is identified as a lookup on (concept, company, fiscal year), the
answer comes from ``data/facts/<TICKER>.jsonl`` — the structured facts
extracted in Phase 2 and verified accurate against the filings' own MD&A
prose (3/3, see results/extraction/report.json). No embedding, no
generation, no chance of a model misreading a figure out of a table.

**Selection is on the fact's own period dates, never on its period label.**
This was found the hard way. The label (``fiscal_period``) is derived from
SEC's ``fy``/``fp`` fields when no normalized frame exists, and those
describe *the filing a fact was reported in*, not the period it covers.
Columbia's FY2023 10-K reports 2021, 2022 and 2023 net income as
comparatives and tags all three ``FY2023FY``; selecting on that label
returned $336.8M (the 2022 comparative) for a 2023 question, against a
verified $348.7M. Glacier was worse — six different values shared the label,
including individual quarters, and the label-based lookup returned $303.2M
against a verified $222.9M.

So: a duration fact answers "fiscal year N" when it starts and ends inside
year N and spans roughly a year; an instant fact answers it when it falls on
that year's end. Balance-sheet concepts (Assets, Deposits,
StockholdersEquity) are instants — a balance at a moment — while
income-statement concepts (NetIncomeLoss, Revenues) are durations.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

__all__ = ["StructuredAnswer", "lookup_fact"]

# FY2023FY / FY2023Q3 / CY2023Q4I — used only for display, never selection.
_PERIOD_RE = re.compile(r"^(?:FY|CY)(\d{4})(FY|Q[1-4])(I?)$")

# A "full year" duration, allowing for 52/53-week fiscal years and filers
# whose year ends a few days either side of December 31.
_MIN_ANNUAL_DAYS = 350
_MAX_ANNUAL_DAYS = 380


@dataclass(frozen=True)
class StructuredAnswer:
    concept: str
    company: str
    fiscal_year: int
    value: float
    unit: str
    fiscal_period: str
    period_type: str
    accession_number: str
    source_url: str
    # Surfaced, not just used internally: "net income for 2023" should be
    # answerable with *which* 2023 — the period the figure actually covers
    # is what makes the answer checkable against the filing.
    period_start: str | None = None
    period_end: str | None = None

    def formatted_value(self) -> str:
        """Render the figure the way a filing would state it."""
        if self.unit == "USD":
            magnitude = abs(self.value)
            if magnitude >= 1e9:
                return f"${self.value / 1e9:.2f} billion"
            if magnitude >= 1e6:
                return f"${self.value / 1e6:.1f} million"
            return f"${self.value:,.2f}"
        if self.unit in {"USD/shares", "USD-per-shares"}:
            return f"${self.value:.2f} per share"
        return f"{self.value:,.2f} {self.unit}"

    def to_dict(self) -> dict:
        return {
            "concept": self.concept,
            "company": self.company,
            "fiscal_year": self.fiscal_year,
            "value": self.value,
            "formatted_value": self.formatted_value(),
            "unit": self.unit,
            "fiscal_period": self.fiscal_period,
            "period_type": self.period_type,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "accession_number": self.accession_number,
            "source_url": self.source_url,
        }


@lru_cache(maxsize=8)
def _load_facts(company: str, facts_dir: str = "data/facts") -> tuple[dict, ...]:
    """Facts for one company, cached — the API answers many queries per
    process and re-reading a 2,400-line file per request is pure waste."""
    path = Path(facts_dir) / f"{company}.jsonl"
    if not path.exists():
        return ()
    return tuple(json.loads(line) for line in path.read_text().splitlines() if line.strip())


def _parse(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def _answers_fiscal_year(fact: dict, fiscal_year: int) -> bool:
    """Does this fact cover the requested fiscal year?

    Durations must both start and end inside the year and span roughly a
    full year — this is what excludes the quarterly figures and the
    prior-year comparatives that share a period label with the annual one.
    Instants must land on the year's end.
    """
    end = _parse(fact.get("period_end"))
    if end is None or end.year != fiscal_year:
        return False

    if fact.get("period_type") == "instant":
        # A year-end balance. Filers close within a few days of Dec 31, and
        # a mid-year instant is a quarter-end, not the annual figure.
        return end.month == 12

    start = _parse(fact.get("period_start"))
    if start is None:
        return False
    return _MIN_ANNUAL_DAYS <= (end - start).days <= _MAX_ANNUAL_DAYS


def _fact_rank(fact: dict) -> tuple:
    """Prefer the **original** filing's figure among equally valid facts.

    A period's figure appears in several filings: once in that year's own
    annual report, then again as a prior-year comparative in later ones.
    Accession numbers embed the filing year, so ascending order puts the
    original first.

    Preferring the original rather than the latest is a deliberate choice,
    and it is the one that matches the corpus. Columbia's 2023 net income is
    reported as **348,715,000** in the FY2023 10-K (accession
    0000887343-24-000089) — the figure its own MD&A states as "$348.7
    million" — and as a rounded **349,000,000** in a 2026 filing
    (0000887343-26-000088), which is also the value SEC promotes into its
    normalized ``CY2023`` frame. Taking the newest would return the rounded
    number and fail the hand-verified ground truth. For due diligence the
    exact as-filed figure, traceable to the filing that first reported it,
    is the more useful answer.

    The trade-off, stated plainly: a genuine *restatement* would also be
    filed later, and this rule returns the superseded original instead.
    Distinguishing a restatement from a rounded comparative needs the
    amended-filing flag, which the companyfacts payload does not carry —
    so the accession number of the answer is surfaced to the caller,
    letting a user see exactly which filing a number came from.
    """
    return (fact.get("accession_number", ""),)


def lookup_fact(
    concept: str, company: str, fiscal_year: int, *, facts_dir: str = "data/facts"
) -> StructuredAnswer | None:
    """Return the best-matching fact, or None if the corpus has no such row.

    Returning None rather than a nearest-year guess is deliberate: the
    caller (``api``/``generate``) falls back to semantic search, which is a
    better outcome than an authoritative-looking figure from the wrong year.
    """
    candidates = [
        fact
        for fact in _load_facts(company, facts_dir)
        if fact["concept"] == concept and _answers_fiscal_year(fact, fiscal_year)
    ]
    if not candidates:
        return None

    best = sorted(candidates, key=_fact_rank)[0]
    return StructuredAnswer(
        concept=best["concept"],
        company=best["company"],
        fiscal_year=fiscal_year,
        value=best["value"],
        unit=best["unit"],
        fiscal_period=best["fiscal_period"],
        period_type=best["period_type"],
        accession_number=best["accession_number"],
        source_url=best["source_url"],
        period_start=best.get("period_start"),
        period_end=best.get("period_end"),
    )
