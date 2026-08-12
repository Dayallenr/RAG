"""
Index-time enrichment of the placeholder document- and section-level chunks.

``chunk_html.py`` deliberately leaves document and section chunks holding
only their heading ("Item 1A. Risk Factors") — structural chunking stays
fast, free, and deterministic, with the content enrichment deferred to
here, right before embedding.

**Why this is deterministic rollup and not LLM summarization.** The
original plan was a generated summary per section. That is arithmetically
impossible on this project's actual budget: 1,442 section + 502 document
chunks against a verified 20-requests/day Gemini free-tier quota is 97 days
of calls. Concatenating the section's own opening paragraphs costs nothing,
re-runs identically in CI, and — for retrieval specifically — is arguably
the better representation anyway, since it embeds the filing's real
language rather than a paraphrase of it.

**Why enrichment matters and isn't cosmetic.** A section chunk whose entire
text is "Item 1A. Risk Factors" is a near-perfect lexical and semantic match
for any question about risk, while carrying no information that could answer
one. Left in the index it is a pure false positive that outranks real
content. Measured on a 500-chunk slice before this module existed, a
heading-only section chunk was the top-scoring dense hit for "What are the
risks of the merger with Umpqua?".

**The one invariant here: ``chunk_id`` is never recomputed.** Ids are
content-addressed over text (``schema.py``), so regenerating one after
rewriting the text would silently break every ``parent_chunk_id`` pointing
at it — the hierarchy would come apart, and the eval set's recorded ids
would stop resolving. Enrichment therefore replaces ``text`` in the
dict that goes to the index and leaves the identity fields alone.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["MAX_SECTION_CHARS", "enrich_placeholder_chunks"]

# bge-small-en-v1.5 truncates at 512 tokens; at roughly 4 characters per
# token that is ~2000 characters. Rolling up more text than the model will
# read wastes indexing time and misrepresents what was actually embedded.
MAX_SECTION_CHARS = 2000

# Document chunks summarize their filing by listing its sections, which is
# short — this cap only guards against a filing with an unusual number of
# them.
MAX_DOCUMENT_CHARS = 2000


def _rollup(texts: list[str], limit: int) -> str:
    """Concatenate texts in order until the character budget is spent.

    Whole units only: a paragraph is either included or it isn't, rather
    than sliced mid-sentence, so the embedded text always reads as real
    filing prose.
    """
    collected: list[str] = []
    used = 0
    for text in texts:
        text = text.strip()
        if not text:
            continue
        if used + len(text) > limit and collected:
            break
        collected.append(text)
        used += len(text) + 2
        if used >= limit:
            break
    return "\n\n".join(collected)


def enrich_placeholder_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return chunks with document/section ``text`` rolled up from children.

    Takes the full narrative chunk list for a corpus (or any self-contained
    subset — a single filing works) because a section's content lives in its
    children, which are separate records. Paragraph, table, and chart chunks
    pass through untouched: their text is already real content.
    """
    children_by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for chunk in chunks:
        if chunk.get("parent_chunk_id"):
            children_by_parent[chunk["parent_chunk_id"]].append(chunk)

    for siblings in children_by_parent.values():
        siblings.sort(key=lambda c: c["chunk_index"])

    enriched: list[dict[str, Any]] = []
    enriched_sections = 0
    empty_sections = 0

    for chunk in chunks:
        chunk_type = chunk["chunk_type"]

        if chunk_type == "section":
            paragraphs = [
                child["text"]
                for child in children_by_parent.get(chunk["chunk_id"], [])
                if child["chunk_type"] == "paragraph"
            ]
            body = _rollup(paragraphs, MAX_SECTION_CHARS)
            if body:
                enriched_sections += 1
                # Heading is kept as the first line: it's the most
                # discriminating text in the chunk ("Item 1A. Risk Factors"
                # is exactly what a section-level query looks like) and
                # dropping it would lose the only signal distinguishing two
                # sections that open with similar boilerplate.
                chunk = {**chunk, "text": f"{chunk['text']}\n\n{body}", "enriched": True}
            else:
                # A section with no child paragraphs above the minimum
                # length — real in 10-Qs, where "Item 3. Defaults Upon
                # Senior Securities" is often a one-line "None." Flagged
                # rather than silently kept: an un-enriched section chunk is
                # still a heading-only false positive, so the indexer drops
                # these instead of embedding them.
                empty_sections += 1
                chunk = {**chunk, "enriched": False}

        elif chunk_type == "document":
            section_names = [
                child["section"]
                for child in children_by_parent.get(chunk["chunk_id"], [])
                if child["chunk_type"] == "section" and child.get("section")
            ]
            if section_names:
                chunk = {
                    **chunk,
                    "text": f"{chunk['text']}\n\n" + _rollup(section_names, MAX_DOCUMENT_CHARS),
                }

        enriched.append(chunk)

    logger.info(
        "enriched %d section chunks; %d had no eligible child paragraphs",
        enriched_sections, empty_sections,
    )
    return enriched
