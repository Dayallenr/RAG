# Engineering notes

A debugging log. Every entry here is a bug or a wrong assumption that real
SEC data found for me — not one I anticipated. Each says what I saw, what
the cause turned out to be, and what I changed. Where my first diagnosis was
wrong I have left the wrong one in, because the wrong turn is usually the
part worth reading.

**Where the numbers come from.** Retrieval and extraction figures are read
straight out of `results/retrieval/report.json` and
`results/extraction/report.json`, and corpus counts off the tracked files in
`data/`. The latency breakdowns and the embedding timings below are
different: they came from a Jaeger trace and from ad-hoc timing runs on this
machine, and there is no report file behind them. They are recorded here as
observations, and I have said so at each one rather than letting them borrow
the credibility of the measured figures.

---

## SEC's `fy`/`fp` fields identify the filing, not the fact

**What I saw.** The structured lookup returned **$336.8M** for Columbia's
2023 net income. The hand-verified figure is **$348.7M**. Glacier was worse:
**$303.2M** returned against a verified **$222.9M**.

**Cause.** Columbia's FY2023 10-K reports 2021, 2022 and 2023 net income
side by side as comparatives, and *all three* carry `fy=2023, fp=FY` in
SEC's companyfacts API. Those fields describe the filing the fact appeared
in, not the period the fact covers — which is obvious in hindsight and not
at all obvious from the field names. `chunk_xbrl.py` fell back to a
`FY{fy}{fp}` period label whenever SEC had not assigned a normalized
`frame`, so all three years became indistinguishable. Two of them then
collided on an identical content-addressed `fact_id` and one silently
overwrote the other. The lookup, keyed on that label, handed back the 2022
comparative. Glacier had six values sharing one label, individual quarters
among them.

**Fix.** Every `StructuredFact` now captures `period_start` and
`period_end`, and both are part of the fingerprint, so two genuinely
different periods can no longer collide. Selection is on actual dates
rather than the label: a duration fact must start and end inside the target
year and span 350–380 days; an instant must fall on the year end.

**What this cost.** It is the single worst class of bug in this project —
no exception, no stack trace, a plausible-looking number, and only
hand-verified ground truth to catch it. It is the reason
`data/extraction_eval_set.jsonl` exists at all.

## A later filing is not automatically a better source

**What I saw.** After fixing the period selection, the same 2023 figure was
still available twice: as `348,700,000` in the original 2023 10-K, and as a
rounded `349,000,000` in a 2026 filing. The rounded one is the value SEC
promotes into its normalized `CY2023` frame, so the obvious rule — trust
the most recent filing, trust the normalized frame — fails against the
hand-verified truth.

**Fix.** `structured_lookup.py` prefers the **earliest** accession, i.e.
the original as-filed figure, and returns the accession number alongside
the value so a reader can see which filing a number came from.

**Downside I accepted.** A genuine restatement is also filed later, and
this rule returns the superseded original for one. Recorded in
`docs/adr/0002-prefer-earliest-accession.md`; I would revisit it if the
corpus ever included a real restatement.

## MPS work does not register as process CPU time

**What I saw.** Two indexing runs appeared to degrade from ~90 chunks/s to
~20 chunks/s partway through.

**What I first concluded, wrongly.** `ps` showed the process at 2.7% CPU. I
read that as the pipeline sitting idle waiting on OpenSearch, and went
looking for a bulk-indexing bottleneck. There wasn't one. The reading was
meaningless: the embedding work runs on the GPU via MPS, which does not
show up as process CPU time at all. Low CPU% does not mean blocked, and I
lost a while to believing it did.

**Actual cause** (timings below are ad-hoc runs on this machine, not a
report file). Both degradation windows lined up exactly with other
corpus-loading Python scripts I had running alongside. The degraded batches
cost ~12s, which is CPU-only speed. Measured cleanly: MPS embeds 256 chunks
in a rock-steady 2.1s across 15 consecutive iterations with zero drift; the
same work on CPU takes ~11s. There is no leak and no accumulating bug — the
pipeline is contention-sensitive on an 8 GB machine and needs the box to
itself.

**Fix.** `scripts/build_index.py` now logs embed seconds and bulk seconds
separately per batch, so the next time this happens the split is readable
straight off the log instead of inferred from a lying process table.

## The 10-Q table of contents leaked into the table corpus

**What I saw.** Tables of contents had been extracted as table chunks,
mostly from South State and Columbia 10-Qs — 53 of them identified in a
corpus of 8,740 table chunks at the time. A TOC is a near-perfect lexical
match for questions about the sections it lists, and answers none of them.

**Cause.** `chunk_tables.py` already excluded TOC-shaped tables, and the
rule worked on 10-Ks. `_ITEM_HEADING_CELL_RE` required whitespace *after*
the item number, which matches a 10-K's `Item 1A. Risk Factors` sitting in
one cell — and never matches a 10-Q, where the number sits alone in its own
column as exactly `Item 1.`. The second half of the problem was scoring:
the exclusion counted matching *cells* against all cells, and in a 10-Q TOC
the `Item N.` cells are only ~14% of the table, diluted below any threshold
that real financial tables survive.

**Fix.** Anchor with `(?:\s|$)`, and score per *row* rather than per cell.
Verified end to end after re-ingestion: **8,671** table chunks on disk,
8,671 in the live index, and **0** TOC-shaped by the current rule. The
tightened row-level scoring removed 69 tables in total rather than the 53
originally identified, so it caught more than the 10-Q shape that motivated
it; I have not gone back through the extra 16 individually. Regression tests cover the 10-K shape, the
10-Q `Item 1.` shape, and a real Glacier en-dash variant
(`tests/test_chunk_tables.py::TestTableOfContentsExclusion`).

## Real filing HTML is messier than any parser I would have written for it

None of these were guesses. Each came from opening a filing that had
produced bad output and reading the markup.

- **The table of contents duplicates every heading.** Every `Item N`
  heading appears twice — once in the TOC, once at the real section. Naive
  detection puts every section boundary at the TOC. Section detection keeps
  only each label's *last* occurrence
  (`chunk_html.py::_real_section_boundaries`).
- **Filing agents disagree about paragraphs.** Workiva output (Columbia)
  contains *zero* `<p>` tags and is div-only; other agents (WesBanco) use
  `<p>` heavily. Paragraph-unit detection has to handle both, which is what
  `chunk_html.py::_leaf_elements` is for.
- **Words are split across inline runs.** Some filers break a single word
  across adjacent `<span>` elements for styling, with no space between them
  — `"RI"` + `"SK"` for `RISK`. Text extraction therefore uses
  `get_text("")`, not `get_text(" ")`; the space-joining version silently
  corrupts headings.
- **8-K item numbering is two-level.** `Item 7.01`, not the 10-K's
  `Item 1A`. The heading regex handles both formats.
- **Most tables are layout, not data.** 140 `<table>` elements counted by
  hand in one real 10-K, of which a small minority carry data. Filtered by shape and
  numeric-cell density. The TOC itself is a real `<table>` that passes a
  naive numeric filter, because page numbers are numeric — it needs the
  separate Item-heading-shaped-row rule above.
- **`colspan` becomes duplicated cells.** pandas expands a spanned cell
  into one copy per column, so a header row serializes as
  `Oregon | Oregon | Oregon`. Collapsed before serialization.

## `pandas.read_html` refuses a decoded string

**What I saw.** `read_html` raised on filings that parsed fine everywhere
else.

**Cause.** These filings declare an XML encoding in their prolog, and lxml
refuses to honour a declared encoding on a Python `str` — by then the
decoding has already happened and it has no way to check the claim.

**Fix.** Pass the raw **bytes**. Worth knowing because the failure looks
like a malformed-document problem and is actually a type problem.

## Section and document chunks were heading-only placeholders

**What I saw.** For "What are the risks of the merger with Umpqua?", the
top-scoring dense hit on a 500-chunk test index was a chunk whose entire
text was `"Item 1A. Risk Factors"`.

**Cause.** Deliberate, and it still bit me. The hierarchical chunker
emitted document and section chunks holding only their heading, with
enrichment deferred to a later phase. All 1,442 section chunks were
heading-only. That is a false-positive factory: a chunk consisting solely
of the words a question is about is a near-perfect embedding match for that
question while containing nothing that answers it, and it outranks the
paragraph that does.

**What I could not do.** The original plan was LLM-generated section
summaries. The arithmetic kills it — 1,944 chunks against a verified
20-requests/day quota on the free tier is 97 days.

**Fix.** `index/enrich.py` rolls a section's own opening paragraphs up into
it at index time. Free, deterministic, reproducible in CI, and it embeds
the filing's real language instead of a paraphrase of it. Sections that
still come out empty — a 10-Q `Item 3. Defaults Upon Senior Securities`
whose entire body is `None.` — are flagged and not indexed at all.

**Sharp edge.** Enrichment must never recompute `chunk_id`. Ids are
content-addressed over text, so regenerating one after changing the text
would silently break every `parent_chunk_id` pointing at it.

## First-request latency is warmup, not steady state

**What I saw**, in a single OTel trace read off Jaeger — one request, not a
distribution, and no report file behind it. The first traced `/ask` after
process start, against the real index, took **2,995 ms**: `embed.query`
1,867 ms, `search.bm25` 541 ms, `search.knn` 209 ms, `rerank` 374 ms.

**Cause.** `rerank` is the only component in that breakdown that is already
at steady state — reranking really does cost hundreds of milliseconds per
query, which the eval run confirms independently. The embedding number is
MPS kernel warmup and the BM25 number is OpenSearch's cold query caches.
Both are one-offs.

**Consequences.** Do not quote 1,867 ms as an embedding latency anywhere —
it is not one. Practically: any load test needs a warmup request first, and
a readiness probe that fires before warmup will see multi-second responses
and may kill the pod.

**Bonus.** The same trace showed the structured route answering in 8.2 ms
with no `retrieve` span and no `generate` span at all — which is the
"no model call on the structured path" claim made visible rather than
asserted.

## The fine-tune does not fit on the machine that serves it

**What I saw.** `scripts/finetune_biencoder.py` calls `resolve_device()`,
which returns `mps` on this Mac, so the script starts and trains without
complaint on Apple Silicon. I took that as evidence the training run could
happen here rather than on the CUDA box, and started it.

**What I first concluded, wrongly.** That the only thing standing between
this repository and a fine-tuned checkpoint was which machine I happened to
be sitting at. The script running is not the same as the run finishing, and
device support says nothing about whether the working set fits.

**Actual cause** (measurements below are ad-hoc runs on this machine, not a
report file — there is no `results/training/report.json`, because no run
completed). The binding constraint is attention activation memory at full
sequence length, not the model. bge-small is 33M parameters, but the mined
passages are long: measured over 1,500 training rows, positives run to a mean
of 217 tokens with p90 at 441, and **6.8% exceed the model's 512-token
window**. `ChunkEmbedder` never lowers `max_seq_length`, so passages are
truncated at 512 when the corpus is indexed — which means training at a
shorter length would be a train/serve skew of exactly the same class as
training without the query prefix, and is not available as a way out.

At 512 tokens, `MultipleNegativesRankingLoss` puts `3 × batch_size` sequences
through the encoder per step, and the attention weights alone come to roughly
7 GB at batch 32. On an 8 GB unified-memory machine:

| batch | outcome |
|---|---|
| 32 | MPS out of memory (8.84 GiB allocated, 9.07 GiB ceiling) |
| 16 | MPS out of memory (9.06 GiB allocated) |
| 8 | runs, by swapping — ~710 s/step |

Batch 8 is the misleading one, because it does not fail. It just goes slowly
enough to be useless: step 1 took 600 s and step 2 took 786 s, so it is
degrading rather than warming up, and 12,758 triplets at batch 8 is 1,595
steps — **about 13 days for a single epoch**. `vm.swapusage` reported 11.2 GB
of a 12 GB swap file in use with 13% of memory free, which is the real story
behind the step times. Batch 8 also costs what the loss is for: in-batch
negatives scale with batch size, so it weakens the contrastive signal at the
same time as it wrecks the throughput.

I had already been warned about this and did not connect it. The note above
about MPS contention, and the 8 GB ceiling flagged for re-embedding and
reranking, are the same machine limit showing up in a third place.

**Fix.** None available here — this is the constraint ADR 0005 anticipated
when it made the training run conditional on a CUDA machine being available,
and the measurement is a vindication of that decision rather than a problem
to solve. Two things changed as a result. `--gradient-checkpointing` is now
wired through the script, because activation memory is the binding constraint
and trading compute for it is the standard fix; it is unit-tested at the
argument seam but has **never completed a training step**, here or anywhere,
and is recorded that way rather than as a solution. And the constraint is
written into the script's own docstring, so the next person to read
`resolve_device()` returning `mps` does not spend an afternoon rediscovering
it.
