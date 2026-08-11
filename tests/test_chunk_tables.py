from __future__ import annotations

from duediligence.ingest.chunk_tables import extract_tables_from_filing

COMMON_KWARGS = dict(
    company="TEST", filing_type="10-K", filing_date="2024-01-01",
    accession_number="0000000000-24-000001", source_url="https://example.com/filing.htm",
    document_chunk_id="doc-abc123",
)

# A real financial table (should survive) and a table-of-contents-shaped
# table (should be excluded) plus a tiny layout table (should be excluded
# for being too small).
SYNTHETIC_HTML = b"""
<html><body>
<table>
<tr><td>State</td><td>Market Share</td><td>Branches</td></tr>
<tr><td>Oregon</td><td>15.78%</td><td>108</td></tr>
<tr><td>Washington</td><td>7.15%</td><td>106</td></tr>
<tr><td>Idaho</td><td>3.70%</td><td>25</td></tr>
</table>

<table>
<tr><td>ITEM 1. BUSINESS</td><td>5</td></tr>
<tr><td>ITEM 1A. RISK FACTORS</td><td>23</td></tr>
<tr><td>ITEM 2. PROPERTIES</td><td>45</td></tr>
<tr><td>ITEM 3. LEGAL PROCEEDINGS</td><td>60</td></tr>
</table>

<table>
<tr><td>X</td><td>Y</td></tr>
</table>
</body></html>
"""


def test_real_financial_table_is_extracted():
    tables = extract_tables_from_filing(SYNTHETIC_HTML, **COMMON_KWARGS)
    assert len(tables) == 1
    assert "Oregon" in tables[0].chunk.text
    assert "15.78%" in tables[0].chunk.text


def test_table_of_contents_shaped_table_is_excluded():
    tables = extract_tables_from_filing(SYNTHETIC_HTML, **COMMON_KWARGS)
    assert not any("RISK FACTORS" in t.chunk.text for t in tables)


def test_tiny_table_is_excluded_by_minimum_shape():
    tables = extract_tables_from_filing(SYNTHETIC_HTML, **COMMON_KWARGS)
    assert not any(t.chunk.text.strip() == "X | Y" for t in tables)


def test_table_chunks_attach_to_the_document_chunk():
    tables = extract_tables_from_filing(SYNTHETIC_HTML, **COMMON_KWARGS)
    assert all(t.chunk.parent_chunk_id == "doc-abc123" for t in tables)
    assert all(t.chunk.chunk_type == "table" for t in tables)


def test_exact_rows_are_preserved_for_verification():
    tables = extract_tables_from_filing(SYNTHETIC_HTML, **COMMON_KWARGS)
    rows = tables[0].rows
    flat = [cell for row in rows for cell in row if cell]
    assert "Oregon" in flat
    assert "15.78%" in flat


def test_colspan_style_duplicate_cells_are_collapsed_in_serialized_text():
    html = b"""
    <html><body><table>
    <tr><td>Oregon</td><td>Oregon</td><td>Oregon</td><td>15.78</td><td>%</td></tr>
    <tr><td>Washington</td><td>Washington</td><td>Washington</td><td>7.15</td><td>%</td></tr>
    <tr><td>Idaho</td><td>Idaho</td><td>Idaho</td><td>3.70</td><td>%</td></tr>
    </table></body></html>
    """
    tables = extract_tables_from_filing(html, **COMMON_KWARGS)
    assert len(tables) == 1
    assert "Oregon | Oregon" not in tables[0].chunk.text
    assert tables[0].chunk.text.splitlines()[0] == "Oregon | 15.78 | %"


def test_no_tables_in_document_returns_empty_list():
    html = b"<html><body><div>No tables here at all.</div></body></html>"
    assert extract_tables_from_filing(html, **COMMON_KWARGS) == []
