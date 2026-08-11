"""
Chart/figure understanding: find genuine chart images in filing HTML,
describe them with Gemini Vision.

Filtering, verified against the real corpus, not assumed
--------------------------------------------------------
A real 10-K/DEF-14A corpus of 502 filings contains 894 <img> tags total —
almost all of them logos, board-member headshots, signature images, and
proxy-voting icons (alt="LOGO" or alt="graphic" on ~95% of them, which
doesn't discriminate). What actually distinguishes a genuine chart is the
filename: SEC filers consistently name real chart images with "chart" or
"graph" in the filename (``performance_graph.jpg``, ``barchart02.jpg``,
``linechart01.jpg``), a convention confirmed by inspecting every image
filename in this corpus. That check finds exactly 11 real charts (stock
performance graphs, compensation bar/line charts) out of 894 — an allowlist
by design: it will under-count charts named unconventionally, but a strict
positive filter beats guessing which of 883 headshots/logos/icons might
secretly be a chart.

Evaluation is qualitative (Phase 3's report), not numeric-precision — see
``duediligence/eval/run_chart_eval.py``. Precise chart digitization (reading
an exact value off a bar) is a genuinely unsolved CV problem; claiming this
pipeline does that precisely would be exactly the kind of unbacked claim
this project is built to avoid.
"""
from __future__ import annotations

import logging
import re
import warnings
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from duediligence.generate.gemini_client import get_client
from duediligence.ingest.schema import Chunk

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

__all__ = ["ChartImageRef", "describe_chart_image", "extract_chart_chunks", "find_chart_image_refs"]

_CHART_FILENAME_RE = re.compile(r"chart|graph", re.IGNORECASE)

_DESCRIPTION_PROMPT = (
    "This image is a figure from a bank's SEC filing (10-K, proxy statement, "
    "or similar). Describe it factually in 2-4 sentences: what type of chart "
    "is it (line, bar, pie, etc.), what does it appear to show (axis labels, "
    "legend categories, general trend direction), and what time period or "
    "categories does it cover if visible. Do not state precise numeric "
    "values you cannot read with confidence — describe the trend and labels, "
    "not exact figures."
)


@dataclass(frozen=True)
class ChartImageRef:
    url: str
    alt_text: str


def find_chart_image_refs(html: str, *, base_url: str) -> list[ChartImageRef]:
    soup = BeautifulSoup(html, "lxml")
    refs = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src or not _CHART_FILENAME_RE.search(src):
            continue
        refs.append(ChartImageRef(url=urljoin(base_url, src), alt_text=(img.get("alt", "") or "").strip()))
    return refs


def _guess_mime_type(url: str) -> str:
    lower = url.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".gif"):
        return "image/gif"
    return "image/jpeg"  # the observed default for this corpus


#: Gemini's free tier is 5 requests/minute for the vision-capable flash
#: model (confirmed by an actual 429 mid-run, not assumed) — retry on
#: RESOURCE_EXHAUSTED rather than losing an image the first time the corpus
#: has more than 5 charts in it.
_RATE_LIMIT_RETRY_SECONDS = 15.0
_MAX_RETRIES = 3


def describe_chart_image(image_bytes: bytes, *, mime_type: str, model: str) -> str:
    import time

    from google.genai import errors, types

    client = get_client()
    contents = [types.Part.from_bytes(data=image_bytes, mime_type=mime_type), _DESCRIPTION_PROMPT]

    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(model=model, contents=contents)
            return (response.text or "").strip()
        except errors.ClientError as error:
            if error.code != 429 or attempt == _MAX_RETRIES:
                raise
            logger.info(
                "rate limited on attempt %d/%d, waiting %.0fs", attempt + 1, _MAX_RETRIES, _RATE_LIMIT_RETRY_SECONDS
            )
            time.sleep(_RATE_LIMIT_RETRY_SECONDS)
    raise AssertionError("unreachable")  # loop always returns or raises


def extract_chart_chunks(
    html: str,
    *,
    company: str,
    filing_type: str,
    filing_date: str,
    accession_number: str,
    source_url: str,
    document_chunk_id: str,
    download_bytes,  # Callable[[str], bytes] — injected so this stays testable without real HTTP/API calls
    vision_model: str,
    skip_urls: frozenset[str] = frozenset(),
) -> list[Chunk]:
    """``skip_urls`` — chart image URLs already described in a previous run.
    The free Gemini tier's vision quota is small enough (confirmed 20
    requests/day on the model this project uses) that re-describing an
    already-done image on every re-run isn't just wasteful, it can burn the
    day's entire remaining budget before reaching genuinely new images."""
    chunks: list[Chunk] = []
    for index, ref in enumerate(find_chart_image_refs(html, base_url=source_url)):
        if ref.url in skip_urls:
            continue
        try:
            image_bytes = download_bytes(ref.url)
            description = describe_chart_image(
                image_bytes, mime_type=_guess_mime_type(ref.url), model=vision_model
            )
        except Exception as error:  # noqa: BLE001 - one bad image must not abort the run
            logger.warning("failed to describe chart image %s: %s", ref.url, error)
            continue
        if not description:
            continue

        chunks.append(
            Chunk(
                company=company, filing_type=filing_type, filing_date=filing_date,
                accession_number=accession_number, source_url=ref.url,
                chunk_type="chart_description", hierarchy_level=2,
                parent_chunk_id=document_chunk_id, chunk_index=index,
                section=None, text=description,
            )
        )
    return chunks
