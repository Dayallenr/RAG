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
    """A human-readable period label — *not* a unique key.

    SEC assigns a normalized ``frame`` (e.g. "CY2023", "CY2023Q4I") to some
    facts but not all. The fallback built from ``fy``/``fp`` is genuinely
    ambiguous and must not be treated as identifying: those two fields
    describe **the filing the fact was reported in**, not the period the
    fact covers. Verified against real data — Columbia's FY2023 10-K
    (accession 0000887343-24-000089) reports three NetIncomeLoss entries,
    for 2021, 2022 and 2023, and all three carry ``fy=2023, fp=FY``:

        start 2021-01-01 end 2021-12-31 val 420,300,000  frame CY2021
        start 2022-01-01 end 2022-12-31 val 336,752,000  (no frame)
        start 2023-01-01 end 2023-12-31 val 348,715,000  (no frame)

    Only ``start``/``end`` separate them, which is why those are captured on
    every fact and are what ``route/structured_lookup.py`` selects on.
    """
    if "frame" in fact:
        return fact["frame"]
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
                        period_start=entry.get("start"),
                        period_end=entry.get("end"),
                    )
                )
    return results
