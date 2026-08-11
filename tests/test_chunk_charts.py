from __future__ import annotations

from unittest.mock import patch

from duediligence.ingest.chunk_charts import (
    _guess_mime_type,
    extract_chart_chunks,
    find_chart_image_refs,
)

HTML_WITH_MIXED_IMAGES = """
<html><body>
<img src="logo_bank.jpg" alt="LOGO">
<img src="sig_johnsmith.jpg" alt="graphic">
<img src="ny2000x1_barchart01.jpg" alt="graphic">
<img src="performance_graph.gif" alt="">
<img src="headshot_janedoe.jpg" alt="graphic">
</body></html>
"""


def test_only_chart_and_graph_named_images_are_found():
    refs = find_chart_image_refs(HTML_WITH_MIXED_IMAGES, base_url="https://www.sec.gov/Archives/edgar/data/1/x/doc.htm")
    urls = [r.url for r in refs]
    assert len(refs) == 2
    assert any("barchart01" in u for u in urls)
    assert any("performance_graph" in u for u in urls)
    assert not any("logo" in u for u in urls)
    assert not any("sig_" in u for u in urls)
    assert not any("headshot" in u for u in urls)


def test_relative_urls_are_resolved_against_the_filing_document_url():
    refs = find_chart_image_refs(
        HTML_WITH_MIXED_IMAGES,
        base_url="https://www.sec.gov/Archives/edgar/data/887343/000114036123017022/def14a.htm",
    )
    barchart = next(r for r in refs if "barchart01" in r.url)
    assert barchart.url == "https://www.sec.gov/Archives/edgar/data/887343/000114036123017022/ny2000x1_barchart01.jpg"


def test_mime_type_guessed_from_extension():
    assert _guess_mime_type("foo/bar_chart01.png") == "image/png"
    assert _guess_mime_type("foo/bar_graph.gif") == "image/gif"
    assert _guess_mime_type("foo/barchart01.jpg") == "image/jpeg"
    assert _guess_mime_type("foo/barchart01") == "image/jpeg"  # unknown extension -> the corpus default


def test_extract_chart_chunks_end_to_end_with_injected_download_and_description():
    def fake_download(url: str) -> bytes:
        return b"fake-image-bytes-for-" + url.encode()

    with patch(
        "duediligence.ingest.chunk_charts.describe_chart_image",
        return_value="A line chart showing total return performance.",
    ) as mock_describe:
        chunks = extract_chart_chunks(
            HTML_WITH_MIXED_IMAGES,
            company="COLB", filing_type="DEF 14A", filing_date="2023-04-06",
            accession_number="0001140361-23-017022",
            source_url="https://www.sec.gov/Archives/edgar/data/887343/000114036123017022/def14a.htm",
            document_chunk_id="doc-xyz", download_bytes=fake_download, vision_model="gemini-flash-latest",
        )

    assert len(chunks) == 2
    assert all(c.chunk_type == "chart_description" for c in chunks)
    assert all(c.parent_chunk_id == "doc-xyz" for c in chunks)
    assert all(c.text == "A line chart showing total return performance." for c in chunks)
    assert mock_describe.call_count == 2


def test_a_failed_image_does_not_abort_the_others():
    call_count = 0

    def flaky_download(url: str) -> bytes:
        nonlocal call_count
        call_count += 1
        if "barchart01" in url:
            raise ConnectionError("simulated network failure")
        return b"fake-bytes"

    with patch(
        "duediligence.ingest.chunk_charts.describe_chart_image", return_value="A chart description."
    ):
        chunks = extract_chart_chunks(
            HTML_WITH_MIXED_IMAGES,
            company="COLB", filing_type="DEF 14A", filing_date="2023-04-06",
            accession_number="0001140361-23-017022",
            source_url="https://www.sec.gov/Archives/edgar/data/887343/000114036123017022/def14a.htm",
            document_chunk_id="doc-xyz", download_bytes=flaky_download, vision_model="gemini-flash-latest",
        )

    # One of the two images fails to download; the other still produces a chunk.
    assert len(chunks) == 1
    assert call_count == 2


def test_no_chart_images_returns_empty_list():
    html = "<html><body><img src='logo.jpg' alt='LOGO'></body></html>"
    chunks = extract_chart_chunks(
        html, company="COLB", filing_type="10-K", filing_date="2024-01-01",
        accession_number="acc-1", source_url="https://example.com/doc.htm",
        document_chunk_id="doc-1", download_bytes=lambda u: b"", vision_model="gemini-flash-latest",
    )
    assert chunks == []
