"""
SEC EDGAR client: ticker -> CIK resolution, filing metadata, XBRL facts,
and filing document downloads.

SEC's access policy (verified against their developer docs, not assumed):
no API key or registration, but every request must carry a real, honest
``User-Agent`` identifying who's asking — requests without one are commonly
rejected with 403 — and the documented rate cap is 10 requests/second.
``config/config.yaml``'s ``edgar.rate_limit_per_second`` defaults to 8,
under that cap with margin rather than hugging the limit.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from duediligence.config import CompanyConfig, EdgarConfig

logger = logging.getLogger(__name__)

__all__ = ["EdgarClient", "FilingMetadata"]


@dataclass(frozen=True)
class FilingMetadata:
    company: str  # ticker
    cik: str  # 10-digit, zero-padded
    accession_number: str  # SEC's permanent per-filing identifier, e.g. "0001628280-23-034239"
    filing_type: str
    filing_date: str
    primary_document: str  # filename of the primary document within the filing
    document_url: str  # full URL to the primary document


class _RateLimiter:
    """Sleeps just enough between calls to stay under N requests/second."""

    def __init__(self, per_second: float) -> None:
        self.min_interval = 1.0 / per_second
        self._last_call: float | None = None

    def wait(self) -> None:
        if self._last_call is not None:
            elapsed = time.monotonic() - self._last_call
            remaining = self.min_interval - elapsed
            if remaining > 0:
                time.sleep(remaining)
        self._last_call = time.monotonic()


class EdgarClient:
    def __init__(self, config: EdgarConfig) -> None:
        self.config = config
        self._session = requests.Session()
        self._session.headers["User-Agent"] = config.user_agent
        self._rate_limiter = _RateLimiter(config.rate_limit_per_second)
        self._ticker_to_cik: dict[str, str] | None = None

    def _get(self, url: str) -> requests.Response:
        self._rate_limiter.wait()
        response = self._session.get(url, timeout=30)
        response.raise_for_status()
        return response

    def resolve_cik(self, ticker: str) -> str:
        """Look up a ticker's 10-digit zero-padded CIK via SEC's public
        ticker->CIK mapping file (fetched once per client, then cached).

        This file only lists currently-active tickers — a company that was
        acquired and delisted drops out of it even though its CIK and
        filing history are permanent. Use ``cik_for`` for any such company
        (set an explicit ``cik`` in its CompanyConfig) rather than this
        method directly.
        """
        if self._ticker_to_cik is None:
            payload = self._get(self.config.ticker_lookup_url).json()
            # payload is {"0": {"cik_str": 320193, "ticker": "AAPL", ...}, "1": {...}, ...}
            self._ticker_to_cik = {
                entry["ticker"].upper(): str(entry["cik_str"]).zfill(10)
                for entry in payload.values()
            }
        try:
            return self._ticker_to_cik[ticker.upper()]
        except KeyError:
            raise KeyError(f"ticker {ticker!r} not found in SEC's ticker lookup") from None

    def cik_for(self, company: CompanyConfig) -> str:
        """CIK for a configured company: the explicit override if set
        (required for delisted/acquired companies), else ticker lookup."""
        if company.cik is not None:
            return company.cik.zfill(10)
        return self.resolve_cik(company.ticker)

    def list_filings(
        self, company: CompanyConfig, *, filing_types: list[str], start_date: str, end_date: str
    ) -> list[FilingMetadata]:
        """Filing metadata for one company, filtered by type and date range.

        Only reads the "recent" filings page from the submissions API —
        correct for these five companies over a ~5 year window (a company
        with a much longer filing history spills into paginated older-filing
        files this doesn't follow; a known, documented scope limit, not a
        silent gap).
        """
        cik = self.cik_for(company)
        submissions = self._get(f"{self.config.data_base_url}/submissions/CIK{cik}.json").json()
        recent = submissions["filings"]["recent"]

        results: list[FilingMetadata] = []
        for index, form in enumerate(recent["form"]):
            filing_date = recent["filingDate"][index]
            if form not in filing_types:
                continue
            if not (start_date <= filing_date <= end_date):
                continue

            accession_number = recent["accessionNumber"][index]
            primary_document = recent["primaryDocument"][index]
            accession_no_dashes = accession_number.replace("-", "")
            document_url = (
                f"{self.config.archives_base_url}/{int(cik)}/{accession_no_dashes}/{primary_document}"
            )
            results.append(
                FilingMetadata(
                    company=company.ticker, cik=cik, accession_number=accession_number,
                    filing_type=form, filing_date=filing_date,
                    primary_document=primary_document, document_url=document_url,
                )
            )
        return results

    def fetch_company_facts(self, company: CompanyConfig) -> dict:
        """Raw XBRL companyfacts payload — every tagged financial fact this
        company has ever reported, across all filings."""
        cik = self.cik_for(company)
        return self._get(f"{self.config.data_base_url}/api/xbrl/companyfacts/CIK{cik}.json").json()

    def download_filing(self, filing: FilingMetadata, destination_dir: Path) -> Path:
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / f"{filing.accession_number}_{filing.primary_document}"
        if not destination.exists():
            response = self._get(filing.document_url)
            destination.write_bytes(response.content)
        return destination

    def download_bytes(self, url: str) -> bytes:
        """Fetch arbitrary content (e.g. an embedded chart image) from
        sec.gov through the same rate-limited, honestly-identified session
        as everything else — SEC's access policy applies to every request
        to their servers, not just the filing/facts endpoints this client
        has dedicated methods for."""
        return self._get(url).content
