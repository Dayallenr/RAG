"""
Structured-vs-semantic query routing.

Two kinds of question arrive at a due-diligence assistant, and they want
completely different machinery:

* **"What was Columbia's net income for FY2023?"** has one exact right
  answer that is already tagged in the filing's XBRL. Retrieving prose and
  asking a model to read a number out of it can only introduce error — the
  number is *in a database*. Route to exact lookup.
* **"Why did Columbia's provision for credit losses increase?"** has no
  tagged answer anywhere. Route to hybrid search over narrative text.

**This is deliberately a deterministic classifier, not an LLM call.** An
LLM router would be a second, unpredictable failure surface in front of a
retrieval system whose whole selling point is traceability, it would cost a
Gemini request per query against a 20/day quota, and its decisions could not
be unit-tested. The rules here are inspectable, free, instant, and every
branch below is covered by a test.

**A structured route requires all three of concept, company, and period**,
because an exact XBRL lookup is a lookup on that composite key. "What was
net income?" names a concept but no company and no year — there is no row
to fetch, so it falls through to semantic search rather than guessing which
of five banks and fifteen years the user meant. Being conservative in this
direction is deliberate: a wrong semantic route returns a passage the user
can read and judge, while a wrong structured route returns an authoritative
looking number for the wrong entity or period.

The concept vocabulary is the **12 concepts actually present** in
data/facts/*.jsonl, not an aspirational list — routing a query to a
structured lookup for a concept the corpus never extracted would produce a
confident "no data" where semantic search would have found the answer in
prose.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

__all__ = ["CONCEPT_SYNONYMS", "Route", "RouteDecision", "classify_query"]


class Route(str, Enum):
    STRUCTURED = "structured"
    SEMANTIC = "semantic"


@dataclass(frozen=True)
class RouteDecision:
    route: Route
    concept: str | None = None
    company: str | None = None
    fiscal_year: int | None = None
    # Human-readable trace of why this route was chosen. Surfaced by the API
    # so a user can see the routing decision rather than having to trust it.
    reasons: list[str] = field(default_factory=list)


# Maps natural phrasing to the XBRL concept names present in the corpus.
# Ordered longest-phrase-first at match time so "net interest income" is not
# shadowed by "interest income".
CONCEPT_SYNONYMS: dict[str, str] = {
    "net income": "NetIncomeLoss",
    "net loss": "NetIncomeLoss",
    "earnings": "NetIncomeLoss",
    "profit": "NetIncomeLoss",
    "total assets": "Assets",
    "assets": "Assets",
    "total liabilities": "Liabilities",
    "liabilities": "Liabilities",
    "deposits": "Deposits",
    "total deposits": "Deposits",
    "shareholders equity": "StockholdersEquity",
    "shareholders' equity": "StockholdersEquity",
    "stockholders equity": "StockholdersEquity",
    "stockholders' equity": "StockholdersEquity",
    "equity": "StockholdersEquity",
    "basic earnings per share": "EarningsPerShareBasic",
    "diluted earnings per share": "EarningsPerShareDiluted",
    "diluted eps": "EarningsPerShareDiluted",
    "basic eps": "EarningsPerShareBasic",
    "earnings per share": "EarningsPerShareBasic",
    "eps": "EarningsPerShareBasic",
    "net interest income": "InterestIncomeExpenseNet",
    "interest and dividend income": "InterestAndDividendIncomeOperating",
    "interest income": "InterestAndDividendIncomeOperating",
    "provision for loan losses": "ProvisionForLoanAndLeaseLosses",
    "provision for loan and lease losses": "ProvisionForLoanAndLeaseLosses",
    "loans and leases receivable": "LoansAndLeasesReceivableNetReportedAmount",
    "net loans": "LoansAndLeasesReceivableNetReportedAmount",
    "revenue": "RevenueFromContractWithCustomerExcludingAssessedTax",
}

COMPANY_ALIASES: dict[str, str] = {
    "colb": "COLB",
    "columbia": "COLB",
    "columbia banking": "COLB",
    "columbia banking system": "COLB",
    "umpq": "UMPQ",
    "umpqua": "UMPQ",
    "umpqua holdings": "UMPQ",
    "gbci": "GBCI",
    "glacier": "GBCI",
    "glacier bancorp": "GBCI",
    "wsbc": "WSBC",
    "wesbanco": "WSBC",
    "ssb": "SSB",
    "southstate": "SSB",
    "south state": "SSB",
}

# Wording that signals the user wants explanation or narrative, not a
# figure. These veto a structured route even when concept/company/year are
# all present: "Why did Columbia's net income fall in 2023?" names all three
# but is emphatically not a lookup.
_NARRATIVE_MARKERS = (
    "why", "how did", "how has", "explain", "describe", "discuss",
    "risk", "risks", "strategy", "outlook", "compare", "drove", "driver",
    "reason", "impact of", "effect of", "changes in", "what caused",
)

_YEAR_RE = re.compile(r"\b(?:fy\s*)?(19\d{2}|20\d{2})\b", re.IGNORECASE)


def _find_concept(text: str) -> tuple[str | None, str | None]:
    """Longest matching synonym wins, so 'net interest income' is not
    mis-detected as 'interest income' (a different XBRL concept)."""
    for phrase in sorted(CONCEPT_SYNONYMS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(phrase)}\b", text):
            return CONCEPT_SYNONYMS[phrase], phrase
    return None, None


def _find_company(text: str) -> str | None:
    for alias in sorted(COMPANY_ALIASES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return COMPANY_ALIASES[alias]
    return None


def classify_query(query: str) -> RouteDecision:
    """Decide whether a query is an exact-value lookup or a narrative search."""
    text = query.lower().strip()
    reasons: list[str] = []

    narrative_hit = next((m for m in _NARRATIVE_MARKERS if m in text), None)
    concept, phrase = _find_concept(text)
    company = _find_company(text)
    year_match = _YEAR_RE.search(text)
    fiscal_year = int(year_match.group(1)) if year_match else None

    if narrative_hit:
        reasons.append(f"narrative marker {narrative_hit!r} — asks for explanation, not a value")
        return RouteDecision(Route.SEMANTIC, concept, company, fiscal_year, reasons)

    if concept:
        reasons.append(f"matched XBRL concept {concept} via {phrase!r}")
    else:
        reasons.append("no XBRL concept in the extracted vocabulary")
    if company:
        reasons.append(f"identified company {company}")
    else:
        reasons.append("no company identified")
    if fiscal_year:
        reasons.append(f"identified fiscal year {fiscal_year}")
    else:
        reasons.append("no fiscal year identified")

    if concept and company and fiscal_year:
        reasons.append("concept + company + period form a complete lookup key")
        return RouteDecision(Route.STRUCTURED, concept, company, fiscal_year, reasons)

    reasons.append("incomplete lookup key — falling back to semantic search")
    return RouteDecision(Route.SEMANTIC, concept, company, fiscal_year, reasons)
