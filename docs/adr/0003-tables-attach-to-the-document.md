# 0003 — Table chunks attach to the document, not to their section

**Status:** accepted

## Context

Narrative chunks form a hierarchy: document → section → paragraph, with each
child carrying a `parent_chunk_id`. Table chunks ought to hang off the
section they physically appear in — a balance sheet under "Item 8. Financial
Statements" is more useful than one floating at document level.

They cannot, cheaply. Tables are extracted with `pandas.read_html`, which
returns a list of DataFrames and discards where in the DOM each one came
from. There is no position to map back onto a section boundary.

## Decision

Table chunks take the document chunk as their parent. This is a documented
scope limit, not an oversight.

## Alternatives considered

- **Re-derive each table's DOM position and match it to a section.**
  Rejected, and this is the whole decision. It means a *second*
  implementation of section-boundary detection, independent of the one in
  `chunk_html.py`. That existing implementation is not simple — it exists
  because the table of contents duplicates every heading, because one filing
  agent emits no `<p>` tags at all, and because filers split words across
  inline `<span>` runs. Two implementations of that logic will drift, and
  the drift will show up as tables attributed to the wrong section: wrong
  answers that look right.
- **Replace `pandas.read_html` with a position-preserving parser.**
  Rejected as disproportionate. `read_html` handles the messy real-world
  markup well and gives exact cell values for free; rewriting table
  extraction to buy a parent pointer is a large change for a small gain.

## Consequences

**Accepted downside.** A table cannot be filtered or ranked by the section
it belongs to, and hierarchical context expansion cannot walk from a table
up to its surrounding narrative. Both are things I would want eventually.

**Why it costs less than it looks.** Table chunks carry the company, filing
type, filing date and accession number, so the metadata filtering that
actually gets used still works. And measured recall@10 on table-ground-truth
questions is 0.425 for BM25 (`results/retrieval/report.json`, 101 of 101
questions human-verified) — the binding constraint there is that serialized
financial tables are numeric soup for a 384-dimensional embedding, not that
their parent pointer is coarse.
