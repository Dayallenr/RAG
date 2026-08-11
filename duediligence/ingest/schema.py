"""
Chunk and structured-fact schemas for the due-diligence corpus.

Content-addressed ``chunk_id`` (same reasoning as a git-commit-hashed
dataset): re-ingesting identical source produces identical ids, so
re-indexing is idempotent and a chunk traces back to exactly the
filing/section/paragraph that produced it.

Hierarchical fields (``parent_chunk_id``, ``hierarchy_level``) support the
document -> section -> paragraph structure: a paragraph chunk's
``parent_chunk_id`` points at its section chunk's id, and a section chunk's
``parent_chunk_id`` points at its document chunk's id (``None`` for the
document-level chunk itself). Retrieval can therefore match a paragraph and
pull in its section-level context without re-embedding that context into
every paragraph under it.

``StructuredFact`` is deliberately a separate type, not another Chunk
variant: an XBRL fact is an exact numeric value with a period and a unit,
not prose to embed and semantically search — see ``duediligence/route/``
for why that distinction drives the retrieval routing decision.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass

__all__ = ["Chunk", "StructuredFact"]


@dataclass(frozen=True)
class Chunk:
    company: str  # ticker
    filing_type: str  # "10-K" | "10-Q" | "8-K" | "DEF 14A" | "S-4"
    filing_date: str  # ISO date
    accession_number: str  # SEC's permanent per-filing identifier
    source_url: str  # real, clickable link back to the filing on sec.gov

    chunk_type: str  # "document" | "section" | "paragraph" | "table" | "chart_description"
    hierarchy_level: int  # 0=document, 1=section, 2=paragraph/table/chart
    parent_chunk_id: str | None
    chunk_index: int  # position among siblings under the same parent
    section: str | None  # e.g. "Item 1A. Risk Factors"

    text: str

    @property
    def chunk_id(self) -> str:
        fingerprint = (
            f"{self.company}:{self.accession_number}:{self.parent_chunk_id}:"
            f"{self.chunk_type}:{self.chunk_index}:{self.text[:100]}"
        )
        return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:16]

    @property
    def token_count(self) -> int:
        return max(1, len(self.text) // 4)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["chunk_id"] = self.chunk_id
        payload["token_count"] = self.token_count
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> Chunk:
        known_fields = {
            "company", "filing_type", "filing_date", "accession_number", "source_url",
            "chunk_type", "hierarchy_level", "parent_chunk_id", "chunk_index", "section", "text",
        }
        return cls(**{key: payload[key] for key in known_fields})


@dataclass(frozen=True)
class StructuredFact:
    """One XBRL-tagged financial fact — an exact value, not prose."""

    company: str  # ticker
    concept: str  # XBRL concept, e.g. "Revenues", "NetIncomeLoss", "Assets"
    value: float
    unit: str  # e.g. "USD"
    fiscal_period: str  # e.g. "CY2023Q4", "CY2023"
    period_type: str  # "instant" | "duration"
    accession_number: str  # the filing this fact was reported in
    source_url: str

    @property
    def fact_id(self) -> str:
        fingerprint = f"{self.company}:{self.concept}:{self.fiscal_period}:{self.accession_number}"
        return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["fact_id"] = self.fact_id
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> StructuredFact:
        known_fields = {
            "company", "concept", "value", "unit", "fiscal_period",
            "period_type", "accession_number", "source_url",
        }
        return cls(**{key: payload[key] for key in known_fields})
