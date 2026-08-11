"""
Find every chart image across the corpus, describe it with Gemini Vision,
and write data/chunks_charts/<ticker>.jsonl.

Reuses each filing's already-computed document chunk id from
data/chunks/<ticker>.jsonl (produced by run_ingestion.py) rather than
recomputing it, so chart chunks attach to the exact same document chunk the
narrative/table chunks do.

Usage:
    python scripts/run_chart_extraction.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.config import load_config
from duediligence.ingest.chunk_charts import extract_chart_chunks
from duediligence.ingest.edgar_client import EdgarClient


def _document_chunk_ids(ticker: str) -> dict[str, str]:
    """accession_number -> document chunk id, from the already-ingested narrative chunks."""
    path = Path(f"data/chunks/{ticker}.jsonl")
    ids = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        chunk = json.loads(line)
        if chunk["chunk_type"] == "document":
            ids[chunk["accession_number"]] = chunk["chunk_id"]
    return ids


def _existing_chart_chunks(out_path: Path) -> list[dict]:
    if not out_path.exists():
        return []
    return [json.loads(line) for line in out_path.read_text().splitlines() if line.strip()]


def main() -> None:
    config = load_config()
    client = EdgarClient(config.edgar)
    manifest = json.loads(Path(config.paths.manifest_path).read_text())

    out_dir = Path("data/chunks_charts")
    out_dir.mkdir(parents=True, exist_ok=True)

    grand_total_new = 0
    grand_total_all = 0
    for entry in manifest["companies"]:
        ticker = entry["ticker"]
        document_chunk_ids = _document_chunk_ids(ticker)
        out_path = out_dir / f"{ticker}.jsonl"

        existing = _existing_chart_chunks(out_path)
        already_done = frozenset(c["source_url"] for c in existing)
        new_chunk_dicts = []
        started = time.perf_counter()

        for filing in entry["filings"]:
            html = Path(filing["local_path"]).read_text(encoding="utf-8", errors="ignore")
            document_chunk_id = document_chunk_ids.get(filing["accession_number"])
            if document_chunk_id is None:
                continue
            new_chunks = extract_chart_chunks(
                html, company=ticker, filing_type=filing["filing_type"],
                filing_date=filing["filing_date"], accession_number=filing["accession_number"],
                source_url=filing["document_url"], document_chunk_id=document_chunk_id,
                download_bytes=client.download_bytes, vision_model=config.models.vision_model,
                skip_urls=already_done,
            )
            new_chunk_dicts.extend(c.to_dict() for c in new_chunks)

        elapsed = time.perf_counter() - started
        combined = existing + new_chunk_dicts
        out_path.write_text("\n".join(json.dumps(c) for c in combined) + "\n" if combined else "")
        grand_total_new += len(new_chunk_dicts)
        grand_total_all += len(combined)
        print(
            f"{ticker:6} +{len(new_chunk_dicts):2} new ({len(combined):2} total)  "
            f"[{elapsed:.1f}s]  -> {out_path}"
        )

    print(f"\ntotal: {grand_total_new} new this run, {grand_total_all} overall")


if __name__ == "__main__":
    main()
