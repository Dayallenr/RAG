"""
Chunk every filing in data/manifest.json: narrative HTML, tables, and XBRL
structured facts. Writes:
    data/chunks/<ticker>.jsonl   — narrative (document/section/paragraph) chunks
    data/tables/<ticker>.jsonl   — table chunks (text) + exact rows (verification)
    data/facts/<ticker>.jsonl    — structured XBRL facts

Usage:
    python scripts/run_ingestion.py
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.ingest.chunk_html import chunk_filing_html
from duediligence.ingest.chunk_tables import ExtractedTable, extract_tables_from_filing
from duediligence.ingest.chunk_xbrl import extract_structured_facts
from duediligence.ingest.schema import Chunk, StructuredFact


def ingest_narrative_and_tables(entry: dict) -> tuple[list[Chunk], list[ExtractedTable]]:
    chunks: list[Chunk] = []
    tables: list[ExtractedTable] = []

    for filing in entry["filings"]:
        path = Path(filing["local_path"])
        html_bytes = path.read_bytes()
        html_text = html_bytes.decode("utf-8", errors="ignore")

        try:
            filing_chunks = chunk_filing_html(
                html_text, company=entry["ticker"], filing_type=filing["filing_type"],
                filing_date=filing["filing_date"], accession_number=filing["accession_number"],
                source_url=filing["document_url"],
            )
            chunks.extend(filing_chunks)
            document_chunk_id = next(c.chunk_id for c in filing_chunks if c.chunk_type == "document")

            tables.extend(
                extract_tables_from_filing(
                    html_bytes, company=entry["ticker"], filing_type=filing["filing_type"],
                    filing_date=filing["filing_date"], accession_number=filing["accession_number"],
                    source_url=filing["document_url"], document_chunk_id=document_chunk_id,
                )
            )
        except Exception as error:  # noqa: BLE001 - one bad filing must not abort the run
            print(f"  ! failed to ingest {filing['accession_number']} ({filing['filing_type']}): {error}")

    return chunks, tables


def ingest_structured_facts(entry: dict) -> list[StructuredFact]:
    facts_payload = json.loads(Path(entry["companyfacts_path"]).read_text())
    return extract_structured_facts(facts_payload, company=entry["ticker"], cik=entry["cik"])


def main() -> None:
    manifest = json.loads(Path("data/manifest.json").read_text())
    chunks_dir = Path("data/chunks")
    tables_dir = Path("data/tables")
    facts_dir = Path("data/facts")
    for directory in (chunks_dir, tables_dir, facts_dir):
        directory.mkdir(parents=True, exist_ok=True)

    grand_total_chunks = Counter()
    grand_total_tables = 0
    grand_total_facts = 0

    for entry in manifest["companies"]:
        started = time.perf_counter()
        chunks, tables = ingest_narrative_and_tables(entry)
        facts = ingest_structured_facts(entry)
        elapsed = time.perf_counter() - started

        (chunks_dir / f"{entry['ticker']}.jsonl").write_text(
            "\n".join(json.dumps(c.to_dict()) for c in chunks) + "\n"
        )
        with (tables_dir / f"{entry['ticker']}.jsonl").open("w") as handle:
            for table in tables:
                handle.write(json.dumps({**table.chunk.to_dict(), "rows": table.rows}) + "\n")
        (facts_dir / f"{entry['ticker']}.jsonl").write_text(
            "\n".join(json.dumps(f.to_dict()) for f in facts) + "\n"
        )

        by_type = Counter(c.chunk_type for c in chunks)
        grand_total_chunks.update(by_type)
        grand_total_tables += len(tables)
        grand_total_facts += len(facts)
        print(
            f"{entry['ticker']:6} {len(chunks):6} narrative chunks {dict(by_type)}  "
            f"{len(tables):4} tables  {len(facts):5} facts  [{elapsed:.1f}s]"
        )

    print(
        f"\ntotal: {sum(grand_total_chunks.values())} narrative chunks "
        f"{dict(grand_total_chunks)}, {grand_total_tables} tables, {grand_total_facts} facts"
    )


if __name__ == "__main__":
    main()
