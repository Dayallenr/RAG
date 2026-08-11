"""
Hierarchical chunking of SEC filing HTML: document -> section -> paragraph.

Two real-world facts about this HTML drove the design (found by actually
inspecting a downloaded filing, not assumed):

1. **No <p> tags.** Modern filings (this corpus is Workiva-generated
   inline-XBRL) use <div>/<span> exclusively. Paragraphs are extracted as
   "leaf" divs — divs with no nested div — above a minimum text length, not
   via semantic paragraph tags that don't exist here.

2. **The table of contents duplicates every "Item N" heading** before the
   real body sections start. A naive first-match-wins section detector
   would treat the TOC as the real sections and misattribute the entire
   document to them. The fix: collect every heading-regex match, and for
   each distinct item label (e.g. "7A") keep only its *last* occurrence in
   the document — the TOC always precedes the body, so the last occurrence
   of a given "Item N. Title" line is the real section start.

Tables are stripped before extraction (handled separately in
``chunk_tables.py``) — mixing raw table-cell text into narrative paragraphs
produces garbled, low-signal chunks.

Document- and section-level chunks hold placeholder text (title/heading)
here, not an LLM-generated summary — that enrichment happens in Phase 4,
right before embedding, not in this structural pass. Keeping structure and
summarization as separate steps means the (fast, free, deterministic)
structural chunking can be tested and iterated on its own.
"""
from __future__ import annotations

import bisect
import logging
import re
import warnings

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from duediligence.ingest.schema import Chunk

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

__all__ = ["chunk_filing_html"]

# Two distinct real item-numbering formats across filing types, both
# handled: 10-K/10-Q/proxy items are "N" or "NA" (e.g. "7A"); 8-K items are
# two-level decimals, "N.NN" (e.g. "7.01" Regulation FD Disclosure, "5.02"
# Departure of Directors) — confirmed against real GBCI/SSB 8-Ks, where the
# original letter-suffix-only pattern split "7.01" into label "7" and left
# ".01" stuck on the front of the title.
_ITEM_HEADING_RE = re.compile(r"^ITEM\s+(\d+(?:\.\d+|[A-Z])?)\.?\s*[-—]?\s*(.*)$", re.IGNORECASE)
_MIN_PARAGRAPH_CHARS = 80


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _leaf_elements(soup: BeautifulSoup):
    """Paragraph-unit elements, in document order.

    Different filing agents produce structurally different HTML: some (e.g.
    Workiva) use <div>/<span> exclusively with no <p> at all; others use
    <p> tags heavily. A <p> is always its own leaf. A <div>/<li> is a leaf
    only if it has no nested <div> *and* no nested <p> — otherwise a
    wrapping div around several <p> children would get yielded as one
    "leaf" whose text is every one of those paragraphs concatenated
    together, silently merging a section heading and the next several
    paragraphs into one blob and breaking heading detection.
    """
    for element in soup.find_all(["div", "li", "p"]):
        if element.name == "p":
            yield element
        elif element.find(["div", "p"]) is None:
            yield element


def _real_section_boundaries(leaves: list[tuple[int, str]]) -> dict[int, tuple[str, str]]:
    """Map {leaf_index: (item_label, title)} for the *last* occurrence of
    each distinct item label — see the module docstring for why "last", not
    "first": it's what skips the table of contents."""
    last_occurrence: dict[str, tuple[int, str]] = {}
    for index, text in leaves:
        match = _ITEM_HEADING_RE.match(text)
        if match:
            label, title = match.group(1).upper(), _normalize(match.group(2))
            last_occurrence[label] = (index, title)
    return {index: (label, title) for label, (index, title) in last_occurrence.items()}


def chunk_filing_html(
    html: str,
    *,
    company: str,
    filing_type: str,
    filing_date: str,
    accession_number: str,
    source_url: str,
) -> list[Chunk]:
    soup = BeautifulSoup(html, "lxml")
    for table in soup.find_all("table"):
        table.decompose()

    # No separator: some filing agents split a single word across adjacent
    # inline <span> runs for styling reasons (e.g. "RI" + "SK" for "RISK",
    # confirmed by inspecting real filing HTML) with no space between them —
    # get_text(' ') would insert a spurious space at every such boundary.
    # Real spacing between runs survives anyway because it's already a
    # literal space/nbsp character inside its own text node.
    leaves = [(index, _normalize(el.get_text(""))) for index, el in enumerate(_leaf_elements(soup))]
    leaves = [(index, text) for index, text in leaves if text]

    boundaries = _real_section_boundaries(leaves)
    boundary_indices = sorted(boundaries)

    chunks: list[Chunk] = []

    document_chunk = Chunk(
        company=company, filing_type=filing_type, filing_date=filing_date,
        accession_number=accession_number, source_url=source_url,
        chunk_type="document", hierarchy_level=0, parent_chunk_id=None, chunk_index=0,
        section=None, text=f"{filing_type} filed by {company} on {filing_date}",
    )
    chunks.append(document_chunk)

    if not boundary_indices:
        # No "Item N" structure detected (common for short 8-Ks, which
        # aren't required to follow the Item-numbered format) — the whole
        # filing becomes paragraph chunks directly under the document chunk,
        # rather than silently producing zero content.
        for para_index, (_, text) in enumerate(
            (i, t) for i, t in leaves if len(t) >= _MIN_PARAGRAPH_CHARS
        ):
            chunks.append(
                Chunk(
                    company=company, filing_type=filing_type, filing_date=filing_date,
                    accession_number=accession_number, source_url=source_url,
                    chunk_type="paragraph", hierarchy_level=2,
                    parent_chunk_id=document_chunk.chunk_id, chunk_index=para_index,
                    section=None, text=text,
                )
            )
        return chunks

    section_chunk_ids: dict[int, str] = {}
    for section_index, boundary_index in enumerate(boundary_indices):
        label, title = boundaries[boundary_index]
        section_name = f"Item {label}. {title}" if title else f"Item {label}."
        section_chunk = Chunk(
            company=company, filing_type=filing_type, filing_date=filing_date,
            accession_number=accession_number, source_url=source_url,
            chunk_type="section", hierarchy_level=1,
            parent_chunk_id=document_chunk.chunk_id, chunk_index=section_index,
            section=section_name, text=section_name,
        )
        chunks.append(section_chunk)
        section_chunk_ids[boundary_index] = section_chunk.chunk_id

    paragraph_index_by_section: dict[int, int] = {}
    for leaf_index, text in leaves:
        if leaf_index in boundaries or len(text) < _MIN_PARAGRAPH_CHARS:
            continue
        # Which section does this paragraph fall under? The last boundary
        # at or before this leaf's position.
        position = bisect.bisect_right(boundary_indices, leaf_index) - 1
        if position < 0:
            continue  # text before the first real section heading (e.g. cover page) — skipped
        boundary_index = boundary_indices[position]
        parent_id = section_chunk_ids[boundary_index]
        label, title = boundaries[boundary_index]
        section_name = f"Item {label}. {title}" if title else f"Item {label}."

        paragraph_index = paragraph_index_by_section.get(boundary_index, 0)
        chunks.append(
            Chunk(
                company=company, filing_type=filing_type, filing_date=filing_date,
                accession_number=accession_number, source_url=source_url,
                chunk_type="paragraph", hierarchy_level=2,
                parent_chunk_id=parent_id, chunk_index=paragraph_index,
                section=section_name, text=text,
            )
        )
        paragraph_index_by_section[boundary_index] = paragraph_index + 1

    return chunks
