from __future__ import annotations

from duediligence.ingest.chunk_html import chunk_filing_html

# Mirrors the real structure found in an actual downloaded filing: no <p>
# tags (div-only), a table-of-contents block that duplicates every "Item N"
# heading before the real body, and a <table> that must not leak into
# paragraph text.
SYNTHETIC_10K_HTML = """
<html><body>
<div>TABLE OF CONTENTS</div>
<div>ITEM 1. BUSINESS</div>
<div>ITEM 1A. RISK FACTORS</div>
<div>ITEM 2. PROPERTIES</div>

<div>ITEM 1. BUSINESS</div>
<div>""" + ("We are a bank holding company operating in the Pacific Northwest region. " * 4) + """</div>
<div>""" + ("Our primary business is commercial and retail banking services. " * 4) + """</div>

<div>ITEM 1A. RISK FACTORS</div>
<div>""" + ("Interest rate risk could materially affect our net interest margin. " * 4) + """</div>
<table><tr><td>Revenue</td><td>1,234,567</td></tr></table>
<div>""" + ("Credit risk from our loan portfolio remains a significant concern. " * 4) + """</div>

<div>ITEM 2. PROPERTIES</div>
<div>""" + ("We lease our headquarters and own several branch locations. " * 4) + """</div>
</body></html>
"""

COMMON_KWARGS = dict(
    company="TEST", filing_type="10-K", filing_date="2024-01-01",
    accession_number="0000000000-24-000001", source_url="https://example.com/filing.htm",
)


def test_toc_duplication_does_not_produce_duplicate_sections():
    chunks = chunk_filing_html(SYNTHETIC_10K_HTML, **COMMON_KWARGS)
    sections = [c for c in chunks if c.chunk_type == "section"]
    labels = [s.section for s in sections]
    # Exactly one section per Item, not two (TOC + body) — this is the whole
    # point of the last-occurrence-per-label heuristic.
    assert labels == ["Item 1. BUSINESS", "Item 1A. RISK FACTORS", "Item 2. PROPERTIES"]


def test_document_chunk_is_root_of_hierarchy():
    chunks = chunk_filing_html(SYNTHETIC_10K_HTML, **COMMON_KWARGS)
    [document_chunk] = [c for c in chunks if c.chunk_type == "document"]
    assert document_chunk.parent_chunk_id is None
    assert document_chunk.hierarchy_level == 0

    sections = [c for c in chunks if c.chunk_type == "section"]
    assert all(s.parent_chunk_id == document_chunk.chunk_id for s in sections)
    assert all(s.hierarchy_level == 1 for s in sections)


def test_paragraphs_are_attributed_to_the_correct_section():
    chunks = chunk_filing_html(SYNTHETIC_10K_HTML, **COMMON_KWARGS)
    sections = {c.section: c for c in chunks if c.chunk_type == "section"}
    paragraphs = [c for c in chunks if c.chunk_type == "paragraph"]

    risk_section_id = sections["Item 1A. RISK FACTORS"].chunk_id
    risk_paragraphs = [p for p in paragraphs if p.parent_chunk_id == risk_section_id]
    assert len(risk_paragraphs) == 2
    assert all("risk" in p.text.lower() or "credit" in p.text.lower() for p in risk_paragraphs)
    assert all(p.hierarchy_level == 2 for p in risk_paragraphs)


def test_table_content_does_not_leak_into_paragraphs():
    chunks = chunk_filing_html(SYNTHETIC_10K_HTML, **COMMON_KWARGS)
    assert not any("1,234,567" in c.text for c in chunks)


def test_paragraph_chunk_indices_are_sequential_within_section():
    chunks = chunk_filing_html(SYNTHETIC_10K_HTML, **COMMON_KWARGS)
    sections = {c.section: c for c in chunks if c.chunk_type == "section"}
    business_id = sections["Item 1. BUSINESS"].chunk_id
    business_paragraphs = sorted(
        (c for c in chunks if c.parent_chunk_id == business_id), key=lambda c: c.chunk_index
    )
    assert [p.chunk_index for p in business_paragraphs] == [0, 1]


def test_8k_two_level_decimal_item_numbers_are_parsed_correctly():
    # 8-Ks use "Item N.NN" (e.g. 7.01 Regulation FD Disclosure), not the
    # 10-K/10-Q "N" or "NA" format — the decimal suffix must stay part of
    # the item label, not get split off into the title.
    html = (
        "<html><body>"
        "<div>ITEM 7.01 REGULATION FD DISCLOSURE</div>"
        "<div>" + ("The company issued a press release regarding quarterly results today. " * 4) + "</div>"
        "<div>ITEM 9.01 FINANCIAL STATEMENTS AND EXHIBITS</div>"
        "<div>" + ("See the exhibit index attached to this report for further details. " * 4) + "</div>"
        "</body></html>"
    )
    chunks = chunk_filing_html(html, **{**COMMON_KWARGS, "filing_type": "8-K"})
    sections = [c.section for c in chunks if c.chunk_type == "section"]
    assert sections == ["Item 7.01. REGULATION FD DISCLOSURE", "Item 9.01. FINANCIAL STATEMENTS AND EXHIBITS"]


def test_filing_with_no_item_structure_falls_back_to_flat_paragraphs():
    html = "<html><body><div>" + ("Board approved a new share repurchase program today. " * 5) + "</div></body></html>"
    chunks = chunk_filing_html(html, **{**COMMON_KWARGS, "filing_type": "8-K"})
    assert not any(c.chunk_type == "section" for c in chunks)
    paragraphs = [c for c in chunks if c.chunk_type == "paragraph"]
    assert len(paragraphs) == 1
    assert paragraphs[0].parent_chunk_id == next(c.chunk_id for c in chunks if c.chunk_type == "document")


def test_chunk_ids_are_stable_across_runs():
    first = chunk_filing_html(SYNTHETIC_10K_HTML, **COMMON_KWARGS)
    second = chunk_filing_html(SYNTHETIC_10K_HTML, **COMMON_KWARGS)
    assert [c.chunk_id for c in first] == [c.chunk_id for c in second]
