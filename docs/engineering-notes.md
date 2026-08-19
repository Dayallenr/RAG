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

## A stale report sat next to the eval it contradicted for six days

**What I saw.** After re-running the retrieval eval against the fully verified
eval set, the ablation report disagreed with it on settings that were supposed
to be identical. Its all-levels configuration should have reproduced the
hybrid retriever's paragraph recall@10 exactly, and did not.

**Cause.** Nothing was wrong with either script. The ablation report had simply
never been re-run after the 10-Q table-of-contents fix changed the corpus
underneath it, so it was scored against an index that no longer existed. It had
been stale for six days, sitting in `results/` next to a report it silently
contradicted, and nothing in the repository could notice: each script writes its
own report and neither reads the other's.

**Fix.** Re-ran it; the two agree exactly (all-levels 0.8286 == hybrid paragraph
recall@10 0.8286). Two findings changed as a result — the chunk hierarchy
crowds the *top ranks* rather than costing recall (recall@1 0.314 -> 0.400
paragraphs-only), and rerank depth peaks at **25** (0.713), not the configured
50.

**The rule this leaves behind:** when the index changes, re-run *every* report
that reads it, not just the headline one. `results/retrieval/report.json` and
`results/ablations/report.json` are both downstream of the corpus, and only one
of them was on anybody's mind.

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
through the encoder per step, and MPS materialises the full attention matrix
rather than streaming it — a 24-sequence forward pass failed asking for exactly
288 MiB, which is `24 × 12 heads × 512² × 4 bytes` to the byte. At batch 32
that is 96 sequences, so 1.125 GiB of attention weights per layer, kept across
all 12 layers for the backward pass. The arithmetic is derived from that one
measured allocation, not separately measured, but it does not need to be
precise to settle the question: the ceiling is 9.07 GiB.

(An earlier version of this note said "roughly 7 GB". That is the figure at
2 bytes per element — i.e. fp16, which this script explicitly refuses off CUDA,
so it was the one precision the run could not use. Corrected rather than
quietly dropped, because it is the same mistake as quoting a warmup latency as
steady state: a number carried over from the wrong condition.)

On an 8 GB unified-memory machine:

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
and trading compute for it is the standard fix; it is tested at the
wiring seam — the test asserts the flag reaches the trainer's arguments, and
was checked by deleting the wiring and watching it fail — but it has **never
been run at the corpus's real sequence length or on a GPU**. It trains a toy
batch, which proves only that gradients flow, and it is recorded as the first
thing to try on the 5070 rather than as a solution. And the constraint is
written into the script's own docstring, so the next person to read
`resolve_device()` returning `mps` does not spend an afternoon rediscovering
it.

## An unchanged metric is not an unchanged result

**What I saw.** I quantised the fine-tuned bi-encoder to INT8, expected to
pay for it in recall, and got a delta table of zeros: recall@1, @5 and @10
identical to PyTorch's on all 101 questions. My first reading was "dynamic
quantisation is free on this corpus", and I nearly wrote that down.

**Cause.** It is not that nothing changed. INT8's query vectors differ from
the fp32 ones (mean cosine 0.9954, minimum 0.9912) and the dense top-20 result
lists differ on **101 of 101 questions** — every single one. recall@k only
asks whether a labelled chunk is inside the top k, so a backend can reorder
every list it returns and score exactly the same. The metrics were unchanged;
the results were not, and those are different claims.

**What I changed.** The benchmark now reports, per arm, how many result lists
are byte-identical to the baseline's alongside the metric deltas, and the
trade-off sentence it generates states both in one breath. I added recall@20 to
the reported metrics, because it was the only metric that moved at all — and
then had to be careful about that one too: **−0.005 is one *label* of a
multi-label question, not one question.** `hit_rate@20` is identical across all
three backends, so at k=20 no question flipped from hit to miss at all; the
only k where one did is k=3 (`hit_rate@3` 0.4158 → 0.4059). I also re-ran the
same benchmark on the 30-question held-out split, where INT8 costs **−0.033
dense recall@10** *and gains* **+0.033 dense recall@1** — one question each
way, which is what one question is worth on thirty. My first write-up of this
quoted only the −0.033, which is the same split-and-metric picking the
paragraph was complaining about.

**And the part that matters most, which I nearly did not measure.** All of the
above is the raw dense path. Through the pipeline this project actually serves
— RRF at dense weight 0.25, candidate depth 50, then the cross-encoder — INT8
scores **+0.000 on every metric with identical reranked lists on all 101
questions**, and on all 30 of the held-out split. Same arithmetic as the
fine-tune's +0.000: the fused pool is BM25's candidate set, so the bi-encoder
reorders a pool whose membership it never changes and the reranker discards the
order. There it destroyed a real gain; here it absorbs a real perturbation.
Quoting the dense degradation alone would have described a configuration nobody
runs.

`results/onnx/report.json` and `results/onnx/test-split.json`.

## The optimised backend is faster per query and much slower per batch

**What I saw.** The first fair timing run had ONNX fp32 at 30 texts/s against
PyTorch's 282 on the corpus sample — the *optimised* runtime, nine times
slower. My first instinct was that the export was broken.

**Cause.** Two separate things, and the first one was my bug. I was feeding
the ONNX session texts in arrival order, so every batch padded up to its
longest member; `sentence_transformers.encode` sorts by length first. Fixing
that — `sorted_batches` in `duediligence/index/onnx_embed.py`, which returns
indices so results scatter back into the caller's order — is worth **1.69x**
on its own: 256 real chunks at batch 32 encode at 13.6 texts/s in arrival
order and 22.9 sorted (an ad-hoc timing on this machine, no report file
behind it). What remains is real and not a bug: the ONNX
backends run on CPU and the PyTorch baseline runs on MPS, so on batch
throughput PyTorch wins by 6.3x even against INT8 — and by 2.0x on CPU against
CPU, which is the comparison that removes the hardware from the question. On
single-query encoding, one short text with no batch to fill, INT8 wins by
3.44x and its p95 falls from 17.0 ms to 3.7 ms. That direction is a runtime
win rather than a hardware one: the benchmark measures a `torch:cpu` arm for
exactly this reason, and PyTorch on CPU is 1.22x *slower* per query than on
MPS.

**Consequence.** The optimisation is for the serving path, not the indexing
path. Re-embedding the corpus with INT8 would take roughly 6.3x longer than
with PyTorch on this machine, so the quantised model is deployed as a query
encoder against an index the fp32 model built — which is what
`results/onnx/report.json` measures, and it says so rather than leaving a
reader to assume both sides were quantised.

## `optimum` would have quietly downgraded transformers

**What I saw.** The obvious way to get ONNX out of a sentence-transformers
model is `SentenceTransformer(..., backend="onnx")`, which needs
`optimum[onnxruntime]`. `pip install --dry-run` resolved it to *downgrading*
`transformers` from 5.15.0 to 4.57.6 and `huggingface_hub` with it.

**Cause.** `optimum` 2.x still pins `transformers>=4.29` with an upper bound
below 5, and pip solved the conflict by moving the installed package rather
than failing.

**What I changed.** Skipped `optimum` entirely. The export is
`torch.onnx.export` over a small wrapper module that reproduces the
checkpoint's own `Transformer -> CLS pooling -> Normalize` stack, and the
quantisation is `onnxruntime.quantization.quantize_dynamic` — `onnx` and
`onnxruntime` install with **no downgrades**. Doing it by hand also made the
pooling assumption explicit and checkable (bge-small pools on CLS, not mean;
`export_onnx` refuses a checkpoint that does not) instead of trusting a
converter to infer it.

## `store.size` measured the directory, not the index

**What I saw.** The ANN sweep (#14) reports the on-disk size of each rebuilt
copy. The first run had `m8-efc256` at **774 MB** and `m16-efc64` at **281 MB**,
for indexes holding the identical 38,483 vectors — a 2.75x spread that no build
parameter could produce, since the HNSW graph is a few MB either way.

**Cause.** `_stats`' `store.size_in_bytes` is the size of the shard directory.
A force merge writes the new segment before the superseded ones are unlinked,
so the directory briefly holds two copies of the corpus, and the reading
depends on when it was taken. Polling until two consecutive readings agreed did
not fix it — both readings can land inside the same stale window, and a merge
still committing can also be caught mid-write and read *low*, which is what the
281 MB was.

**What I changed.** Size is summed from the segments API, which lists live
segments only. Across the whole 9-cell grid it then reads 357.7-358.1 MB — a
0.12% spread, which is the graph, and it matches the raw arithmetic (38,483 x
384 floats, stored once by the HNSW format and again as doc values). The
`store.size` figure is still reported beside it as `store_size_bytes`, so the
gap between the two is inspectable rather than a claim in a docstring.

## A faithful index copy still reorders results

**What I saw.** Every `_reindex` copy in the build grid was checked by running
*exact* search on it and comparing against exact search on the source — same
vectors must mean same ranking. Up to 10 of 101 queries came back in a
different order. That is the signature of a lossy copy, and it would have
invalidated the whole grid.

**Cause.** Ties. These filings repeat boilerplate verbatim across companies and
quarters, so genuinely distinct chunks score identically, and Lucene breaks a
score tie on internal document id — which a 7-segment source and a force-merged
1-segment copy do not share. Where a tie straddles the k-th place, which
document makes the cut is arbitrary in *both* indexes.

**What I changed.** The check classifies each query `identical`, `tied`, or
`different` (`compare_exact_lists`): same set with every disagreeing position
holding equal scores is `tied`; a symmetric difference whose members all score
at the cut is `tied`; anything else is `different`. `different: 0` on all nine
copies is the number the grid rests on, and it is now the one reported. The
same fact bounds the ANN recall figures slightly: a graph that returned the
other member of a tie is scored as having missed.

## One HNSW build does not measure one HNSW configuration

**What I saw.** In the 9-cell `(m, ef_construction)` grid, `m16-efc64` was stuck
at **0.912** ANN recall even at `ef_search=800`, while every other cell reached
≥0.991. Read naively, that is a build parameter failing.

**Cause.** It was not reproducible. The same configuration rebuilt twice more,
unchanged, gave **0.996** and **0.961** — a build-to-build spread of 0.084,
wider than the gaps between the grid's cells. HNSW construction is randomised
(layer assignment and neighbour selection), so with one build per cell the grid
ranks which cell got the lucky graph alongside which parameters help.

**What I changed.** Nothing in the code — the honest fix is in what the result
is allowed to claim. The grid is reported as the range these parameters live in
rather than a ranking of them, the two rebuilds are committed as artifacts
beside the report, and the conclusion that does survive is the one the
search-time curve made independently: on this corpus `ef_search` is where the
recall is.
