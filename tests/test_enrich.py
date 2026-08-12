"""Tests for index-time enrichment of placeholder document/section chunks."""
from __future__ import annotations

from duediligence.index.enrich import MAX_SECTION_CHARS, enrich_placeholder_chunks


def _chunk(chunk_id, chunk_type, text, *, parent=None, index=0, section=None):
    return {
        "chunk_id": chunk_id,
        "chunk_type": chunk_type,
        "text": text,
        "parent_chunk_id": parent,
        "chunk_index": index,
        "section": section,
    }


def _corpus():
    return [
        _chunk("doc1", "document", "10-K filed by COLB on 2024-02-29"),
        _chunk("sec1", "section", "Item 1A. Risk Factors", parent="doc1", index=0,
               section="Item 1A. Risk Factors"),
        _chunk("p2", "paragraph", "Second paragraph about interest rate risk.",
               parent="sec1", index=1),
        _chunk("p1", "paragraph", "First paragraph about credit risk.",
               parent="sec1", index=0),
    ]


class TestSectionEnrichment:
    def test_section_gains_child_paragraph_text(self):
        result = {c["chunk_id"]: c for c in enrich_placeholder_chunks(_corpus())}
        section = result["sec1"]
        assert "credit risk" in section["text"]
        assert "interest rate risk" in section["text"]
        assert section["enriched"] is True

    def test_heading_is_kept_as_the_first_line(self):
        result = {c["chunk_id"]: c for c in enrich_placeholder_chunks(_corpus())}
        assert result["sec1"]["text"].startswith("Item 1A. Risk Factors")

    def test_children_are_rolled_up_in_chunk_index_order(self):
        # The corpus above lists p2 before p1 on purpose — rollup must sort
        # by chunk_index, not rely on file order.
        text = {c["chunk_id"]: c for c in enrich_placeholder_chunks(_corpus())}["sec1"]["text"]
        assert text.index("credit risk") < text.index("interest rate risk")

    def test_section_without_children_is_flagged_not_enriched(self):
        chunks = [
            _chunk("doc1", "document", "10-Q filed by SSB on 2024-05-01"),
            _chunk("sec1", "section", "Item 3. Defaults Upon Senior Securities",
                   parent="doc1", section="Item 3. Defaults Upon Senior Securities"),
        ]
        result = {c["chunk_id"]: c for c in enrich_placeholder_chunks(chunks)}
        assert result["sec1"]["enriched"] is False
        assert result["sec1"]["text"] == "Item 3. Defaults Upon Senior Securities"

    def test_rollup_respects_the_character_budget(self):
        chunks = [_chunk("sec1", "section", "Item 1. Business", section="Item 1. Business")]
        chunks += [
            _chunk(f"p{i}", "paragraph", "x" * 500, parent="sec1", index=i)
            for i in range(20)
        ]
        section = {c["chunk_id"]: c for c in enrich_placeholder_chunks(chunks)}["sec1"]
        # Budget applies to the rolled-up body; the heading rides along on top.
        assert len(section["text"]) <= MAX_SECTION_CHARS + len("Item 1. Business") + 2

    def test_oversized_single_paragraph_is_kept_whole(self):
        # Rollup takes whole paragraphs only. A first child larger than the
        # budget must still be included rather than producing an empty body
        # that would leave the section a bare heading.
        chunks = [
            _chunk("sec1", "section", "Item 1. Business", section="Item 1. Business"),
            _chunk("p1", "paragraph", "y" * (MAX_SECTION_CHARS * 2), parent="sec1", index=0),
        ]
        section = {c["chunk_id"]: c for c in enrich_placeholder_chunks(chunks)}["sec1"]
        assert section["enriched"] is True
        assert "y" * 100 in section["text"]


class TestDocumentEnrichment:
    def test_document_lists_its_section_headings(self):
        result = {c["chunk_id"]: c for c in enrich_placeholder_chunks(_corpus())}
        assert "Item 1A. Risk Factors" in result["doc1"]["text"]
        assert result["doc1"]["text"].startswith("10-K filed by COLB")


class TestInvariants:
    def test_chunk_ids_are_never_rewritten(self):
        # Ids are content-addressed over text; regenerating one after
        # enrichment would break every parent_chunk_id pointing at it.
        original = _corpus()
        enriched = enrich_placeholder_chunks(original)
        assert [c["chunk_id"] for c in enriched] == [c["chunk_id"] for c in original]
        assert [c["parent_chunk_id"] for c in enriched] == [c["parent_chunk_id"] for c in original]

    def test_input_chunks_are_not_mutated(self):
        original = _corpus()
        enrich_placeholder_chunks(original)
        assert original[1]["text"] == "Item 1A. Risk Factors"

    def test_paragraph_chunks_pass_through_untouched(self):
        result = {c["chunk_id"]: c for c in enrich_placeholder_chunks(_corpus())}
        assert result["p1"]["text"] == "First paragraph about credit risk."
