"""
Table extraction from SEC filing HTML via pandas.read_html.

Two real gotchas found by actually running this against a downloaded filing,
not assumed:

1. **pandas needs bytes, not a decoded str.** These filings declare an XML
   encoding (``<?xml version='1.0' encoding='ASCII'?>``), and lxml refuses
   to honor a declared encoding on a Python ``str`` — it raises
   "Unicode strings with encoding declaration are not supported." Passing
   the raw bytes (``io.BytesIO``, not a decoded string) sidesteps this;
   BeautifulSoup's parser in ``chunk_html.py`` is more lenient about it, so
   this bit only had to be dealt with here.

2. **Most tables aren't data tables.** SEC filings use HTML tables
   pervasively for layout (checkboxes, cover-page formatting) — a real 10-K
   had 140 raw tables, and only a handful were genuine financial tables.
   Filtered by shape (>=3 rows, >=2 cols) and a numeric-cell-density
   threshold, verified empirically against real filings to reliably surface
   real financial tables (loan balances, interest rate tables, fair value
   disclosures) while dropping layout tables.

3. **colspan expansion duplicates cells, and the table of contents itself
   passes the numeric filter.** These filings use heavy colspan for visual
   spacing, which pandas expands into repeated identical values across
   columns ("Oregon | Oregon | Oregon" for one merged cell) — collapsed here
   so serialized text is readable instead of stuttering. The table-of-
   contents page itself is a real HTML `<table>` whose page numbers are
   "numeric" enough to pass the density filter; caught separately by
   recognizing rows that are mostly "Item N. Title"-shaped text, reusing
   ``chunk_html``'s heading pattern.

Tables aren't attributed to their surrounding section — pandas.read_html
doesn't preserve DOM position, and re-deriving it would mean duplicating
``chunk_html.py``'s section-boundary logic against a second, independent
traversal that could drift out of sync with it. Table chunks attach directly
to the document chunk instead — a documented scope limit, not a silent gap.

Exact cell values are preserved separately (not just the serialized text
used for embedding) so Phase 2's extraction-accuracy eval can check a
parsed value against the real filing without re-parsing anything.
"""
from __future__ import annotations

import io
import logging
import re
import warnings
from dataclasses import dataclass

import pandas as pd

from duediligence.ingest.schema import Chunk

logger = logging.getLogger(__name__)

__all__ = ["ExtractedTable", "extract_tables_from_filing"]

_NUMERIC_CELL_RE = re.compile(r"^\(?\$?[\d,]+\.?\d*%?\)?$")
# Reuses chunk_html's heading shape (not the compiled pattern itself, to
# keep this module independent) to recognize "this row is a table-of-
# contents entry," e.g. "ITEM 1A. RISK FACTORS".
#
# The trailing `(?:\s|$)` matters and was a real bug. 10-K tables of
# contents put the whole heading in one cell ("Item 1A. Risk Factors"), so a
# required trailing space matched. 10-Q tables of contents put the number in
# its own column, making the cell exactly "Item 1." with nothing after it —
# the space never matched, and 53 of 8,740 table chunks were 10-Q tables of
# contents indexed as though they were financial tables.
_ITEM_HEADING_CELL_RE = re.compile(r"^ITEM\s+\d+(?:\.\d+|[A-Z])?\.?(?:\s|$)", re.IGNORECASE)

_MIN_ROWS = 3
_MIN_COLS = 2
_MIN_NUMERIC_FRACTION = 0.15

# Fraction of *rows* containing an Item heading, not fraction of cells.
#
# Measured, not guessed. The original cell-based threshold could not
# separate the two populations: in a 10-Q table of contents the "Item N."
# cells are only ~14% of all cells (the titles and page numbers dominate),
# well under any threshold that genuine financial tables would survive.
# Counting rows instead separates them cleanly — across all 8,740 extracted
# tables, genuine ones sit at 0.000 even at the 99th percentile, while every
# table of contents is at 0.268 or above. 0.25 sits in that gap and catches
# 69 tables of contents while rejecting no genuine table.
_MAX_ITEM_HEADING_ROW_FRACTION = 0.25


@dataclass(frozen=True)
class ExtractedTable:
    """A table chunk plus its exact cell values, kept alongside the Chunk
    (whose ``text`` is a lossy text serialization, good for embedding, not
    for verifying an exact number)."""

    chunk: Chunk
    rows: list[list[str | None]]


def _dedup_consecutive(cells: list[str]) -> list[str]:
    """Collapse runs of identical adjacent values — the artifact of pandas
    expanding an HTML colspan into repeated cells, not real repeated data."""
    result: list[str] = []
    for cell in cells:
        if not result or result[-1] != cell:
            result.append(cell)
    return result


def _cleaned_rows(frame: pd.DataFrame) -> list[list[str]]:
    rows = []
    for _, row in frame.iterrows():
        cells = [str(value).strip() for value in row.to_numpy()]
        cells = [c for c in cells if c and c.lower() != "nan"]
        cells = _dedup_consecutive(cells)
        if cells:
            rows.append(cells)
    return rows


def _is_data_table(rows: list[list[str]]) -> bool:
    if len(rows) < _MIN_ROWS:
        return False
    all_cells = [cell for row in rows for cell in row]
    if len(all_cells) < _MIN_ROWS * _MIN_COLS:
        return False

    numeric = sum(1 for c in all_cells if _NUMERIC_CELL_RE.match(c.replace(" ", "")))
    if numeric / len(all_cells) < _MIN_NUMERIC_FRACTION:
        return False

    # A table of contents passes the numeric check above (page numbers are
    # "numeric"), so it needs this separate, explicit exclusion. Scored per
    # row — a row counts once if any of its cells is an Item heading —
    # because the per-cell version is diluted to nothing by the title and
    # page-number cells that make up most of a table of contents.
    heading_rows = sum(1 for row in rows if any(_ITEM_HEADING_CELL_RE.match(c) for c in row))
    if heading_rows / len(rows) > _MAX_ITEM_HEADING_ROW_FRACTION:
        return False

    return True


def _serialize_for_embedding(rows: list[list[str]]) -> str:
    """Lossy but readable: one line per row, deduped non-empty cells joined.
    Good enough for semantic search to match against; not a rendering of
    the original table."""
    return "\n".join(" | ".join(row) for row in rows)


def _rows_as_json_safe(frame: pd.DataFrame) -> list[list[str | None]]:
    rows = []
    for _, row in frame.iterrows():
        rows.append([None if pd.isna(v) else str(v) for v in row.to_numpy()])
    return rows


def extract_tables_from_filing(
    html_bytes: bytes,
    *,
    company: str,
    filing_type: str,
    filing_date: str,
    accession_number: str,
    source_url: str,
    document_chunk_id: str,
) -> list[ExtractedTable]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            frames = pd.read_html(io.BytesIO(html_bytes), flavor="lxml")
        except ValueError:
            # pandas raises ValueError "No tables found" for filings with no
            # <table> elements at all (rare, but real for some short 8-Ks).
            return []

    results: list[ExtractedTable] = []
    table_index = 0
    for frame in frames:
        cleaned = _cleaned_rows(frame)
        if not _is_data_table(cleaned):
            continue
        text = _serialize_for_embedding(cleaned)
        if not text:
            continue
        chunk = Chunk(
            company=company, filing_type=filing_type, filing_date=filing_date,
            accession_number=accession_number, source_url=source_url,
            chunk_type="table", hierarchy_level=2, parent_chunk_id=document_chunk_id,
            chunk_index=table_index, section=None, text=text,
        )
        results.append(ExtractedTable(chunk=chunk, rows=_rows_as_json_safe(frame)))
        table_index += 1

    return results
