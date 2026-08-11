"""
XBRL structured financial facts — kept as ``StructuredFact`` records, not
embedded prose ``Chunk``s.

The point of pulling these out separately: "what was Company X's net income
in Q1 2023" has an exact, structured answer that should never go through
semantic retrieval — see ``duediligence/route/`` for the routing decision
this enables.

``BANK_CONCEPTS`` is a curated list of standard ``us-gaap`` taxonomy
concepts, each individually verified present in a real downloaded
``companyfacts.json`` (Columbia Banking System) before being added — not
guessed. Company-specific extension-taxonomy concepts (each filer reports
hundreds) are out of scope: they aren't comparable across companies, which
is the whole point of a due-diligence tool that spans several banks.

A single (concept, period) pair legitimately appears multiple times across
different filings — a 2010 Q1 net income figure gets re-reported in every
subsequent 10-K/10-Q that shows it as a prior-period comparison. These are
kept as separate facts (each tied to the accession number that reported it,
which is part of ``StructuredFact.fact_id``), not deduplicated — a real due-
diligence question can be "what did the original filing say" vs. "what did
a later filing restate this to," and collapsing them would silently lose
that distinction.
"""
from __future__ import annotations

import logging

from duediligence.ingest.schema import StructuredFact

logger = logging.getLogger(__name__)

__all__ = ["BANK_CONCEPTS", "extract_structured_facts"]

BANK_CONCEPTS: tuple[str, ...] = (
    "Assets",
    "Liabilities",
    "StockholdersEquity",
    "Deposits",
    "NetIncomeLoss",
    "InterestAndDividendIncomeOperating",
    "InterestIncomeExpenseNet",
    "LoansAndLeasesReceivableNetReportedAmount",
    "ProvisionForLoanAndLeaseLosses",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "EarningsPerShareBasic",
    "EarningsPerShareDiluted",
)


def _fiscal_period(fact: dict) -> str:
    if "frame" in fact:
        return fact["frame"]
    # SEC doesn't always assign a normalized "frame" label (seen for some
    # non-calendar-aligned or amended periods) — fall back to an equivalent
    # built from fy/fp rather than dropping the fact.
    return f"FY{fact.get('fy', '?')}{fact.get('fp', '')}"


def _filing_index_url(cik: str, accession_number: str) -> str:
    accession_no_dashes = accession_number.replace("-", "")
    return (
        f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
        f"{accession_no_dashes}/{accession_number}-index.htm"
    )


def extract_structured_facts(
    companyfacts: dict, *, company: str, cik: str, concepts: tuple[str, ...] = BANK_CONCEPTS
) -> list[StructuredFact]:
    gaap = companyfacts.get("facts", {}).get("us-gaap", {})
    results: list[StructuredFact] = []

    for concept in concepts:
        concept_data = gaap.get(concept)
        if concept_data is None:
            logger.info("concept %s not reported by %s", concept, company)
            continue
        for unit, entries in concept_data.get("units", {}).items():
            for entry in entries:
                results.append(
                    StructuredFact(
                        company=company,
                        concept=concept,
                        value=float(entry["val"]),
                        unit=unit,
                        fiscal_period=_fiscal_period(entry),
                        period_type="duration" if "start" in entry else "instant",
                        accession_number=entry["accn"],
                        source_url=_filing_index_url(cik, entry["accn"]),
                    )
                )
    return results
