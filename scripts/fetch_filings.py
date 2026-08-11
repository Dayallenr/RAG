"""
Fetch real SEC filings + XBRL facts for every company in config/config.yaml
and write data/manifest.json.

Respects SEC's rate limit and User-Agent policy via EdgarClient. Idempotent:
already-downloaded filing documents are not re-fetched.

Usage:
    python scripts/fetch_filings.py
"""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.config import load_config
from duediligence.ingest.edgar_client import EdgarClient


def main() -> None:
    config = load_config()
    client = EdgarClient(config.edgar)
    filings_dir = Path(config.paths.filings_dir)

    manifest = {"fetched_at": datetime.now(UTC).isoformat(), "companies": []}

    for company in config.companies:
        print(f"{company.ticker} ({company.name}):")

        filings = client.list_filings(
            company,
            filing_types=config.filing_types,
            start_date=config.date_range["start"],
            end_date=config.date_range["end"],
        )
        company_dir = filings_dir / company.ticker
        downloaded = []
        for filing in filings:
            local_path = client.download_filing(filing, company_dir)
            downloaded.append(
                {
                    "accession_number": filing.accession_number,
                    "filing_type": filing.filing_type,
                    "filing_date": filing.filing_date,
                    "document_url": filing.document_url,
                    "local_path": str(local_path),
                }
            )
            print(f"  {filing.filing_type:8} {filing.filing_date}  {filing.accession_number}")

        facts = client.fetch_company_facts(company)
        facts_path = company_dir / "companyfacts.json"
        facts_path.parent.mkdir(parents=True, exist_ok=True)
        facts_path.write_text(json.dumps(facts))
        fact_concepts = sum(len(taxonomy) for taxonomy in facts.get("facts", {}).values())

        manifest["companies"].append(
            {
                "ticker": company.ticker,
                "name": company.name,
                "cik": client.cik_for(company),
                "filings": downloaded,
                "companyfacts_path": str(facts_path),
                "companyfacts_concept_count": fact_concepts,
            }
        )
        print(f"  {len(downloaded)} filings, {fact_concepts} XBRL concepts\n")

    manifest_path = Path(config.paths.manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {manifest_path}")


if __name__ == "__main__":
    main()
