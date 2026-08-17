# Bank M&A Due-Diligence RAG — project rules and status

Portfolio project for Dayallen Ragunathan (SWE + ML roles) — versatile by
design: strong enough on the ML side (real retrieval eval, hybrid search,
structured extraction) for the ML resume, and strong enough on the SWE side
(served API, containers, Kubernetes, IaC, CI/CD) for the SWE resume.
This file loads every session. Read it before doing anything.

---

## Prime directive: truthfulness over convenience

Same rule as this user's other project (PathFinder): every claim in the
README/resume must correspond to real working code and a reproducible
artifact — a script, a report JSON, a plot, a logged metric. If a claim
can't be made true without unreasonable effort, say so explicitly. Never
report a number you have not personally seen produced. A single invented
figure destroys the whole project's credibility.

This has already mattered concretely once: a reference write-up this
project's design was partly inspired by claimed Qwen was "85% cheaper than
GPT-4o" — checked, and Qwen isn't even on Groq's free tier (paid preview,
$0.60/$3.00 per 1M tokens). Don't repeat unverified claims from blog posts
just because they sound authoritative — verify or cut.

---

## What this project is

A due-diligence assistant over **real SEC EDGAR filings**, centered on
**Columbia Banking System's real 2023 merger of equals with Umpqua
Holdings** (independently fact-checkable against real news coverage and the
real merger proxy), plus three more standalone regional banks (Glacier
Bancorp, WesBanco, South State) for corpus breadth. Not synthetic data, not
a toy dataset — 502 real filings, fetched live from SEC's public API.

Three real, distinct data-extraction paths (the "custom parsing pipeline"
story): narrative HTML (hierarchical document→section→paragraph), tables
(`pandas.read_html`), and XBRL structured financial facts (SEC's
companyfacts API) — plus chart/figure understanding via Gemini Vision on top
of that. A structured-vs-semantic query router (not yet built) will send
factual/numeric questions to exact XBRL lookup and narrative questions to
hybrid search — a real, testable routing decision, not an LLM judgment call.

---

## Locked-in scope decisions — do not re-litigate these

- **No fine-tuning.** Embedding + reranker models are self-hosted,
  inference-only (`sentence-transformers`). User explicitly declined
  reopening this after a reference write-up suggested it. Keeps the project
  GPU-independent — runs entirely on the Mac.
- **Storage: OpenSearch**, one engine for both BM25 and k-NN vector search.
  Self-hosted via Docker for local dev/CI ($0). AWS OpenSearch Service for
  one gated, money-costing real-cloud demo late in the project — **never
  apply Terraform for this without the user's explicit real-time go-ahead**,
  same discipline as PathFinder's EKS phase (see PathFinder's CLAUDE.md if
  you want the fuller reasoning for why this discipline exists).
- **FastAPI, not gRPC** — deliberately diversified from PathFinder's stack
  so the user's two projects don't read as one repeated pattern.
- **Generation + vision model: Gemini free tier** (`gemini-flash-latest` —
  see the Environment section below for why not a pinned version, and why
  not Groq/Qwen).
- **Tables attach to the document chunk, not their surrounding section** —
  `pandas.read_html` doesn't preserve DOM position; re-deriving it would
  mean a second, independent section-boundary implementation that could
  drift from the one in `chunk_html.py`. Documented scope limit, not a bug.
- **SageMaker/fine-tuning-adjacent AWS services**: out of scope entirely for
  this project (no ML training infra needed given the no-fine-tuning
  decision above).

---

## Environment

| | |
|---|---|
| Repo | `/Users/dayallenragunathan/CodingProjects/RAG` — remote `github.com/Dayallenr/RAG` (public). Issues/specs live in its GitHub Issues; `gh` is installed but needs `GH_CONFIG_DIR=$HOME/.gh` (set in `~/.zshenv`) because `~/.config` is root-owned. |
| Python | 3.13.5, venv at `.venv/` |
| Secrets | `.env` (gitignored) holds a **real, working** `GOOGLE_API_KEY`. `.env.example` is the tracked placeholder. |
| Gemini model | `gemini-flash-latest`, **not** a pinned version — `gemini-2.5-flash` was confirmed dead ("no longer available to new users") on this API key despite still appearing in the model list. The `-latest` alias tracks whatever Google currently recommends. |
| Gemini free tier quota | **20 requests/day** for the vision-capable flash model on this key (confirmed by an actual 429, not documentation) — not just a per-minute limit. Any script calling Gemini must be idempotent/resumable (see `scripts/run_chart_extraction.py`'s `skip_urls` pattern) or you'll burn the day's quota re-doing finished work. |
| AWS | User has ~$100 in credits, same budget pool as PathFinder. Zero-spend by default; real AWS OpenSearch Service only for one short, gated, explicitly-approved demo late in the project. |
| Local OpenSearch | `docker compose -f docker/docker-compose.yml up -d` → `http://localhost:9200`. Pinned 2.19.1, security plugin off, k-NN plugin confirmed present. Data lives in a named Docker volume and **survives container restarts** — a rebuilt index is not lost when Docker Desktop stops. |

Always run `ruff check .` and `pytest` before claiming work is done.

---

## Established findings — do not re-derive these, they're already verified

**SEC EDGAR access**: free, no API key/registration, but requires an honest
`User-Agent: "name email@example.com"` header (else 403) and respects a
documented 10 req/sec cap (`EdgarClient` uses 8/sec with margin).

**Umpqua Holdings (UMPQ) was acquired and delisted in 2023** — dropped out
of SEC's current ticker→CIK lookup file even though its CIK (`1077771`) and
filing history are permanent. `CompanyConfig.cik` is an explicit override
for exactly this case; don't assume ticker resolution works for every
company.

**Real filing HTML is genuinely messy, confirmed by inspection, not
assumed**:
- The Table of Contents duplicates every "Item N" heading before the real
  body — section detection keeps only each label's *last* occurrence
  (`chunk_html.py::_real_section_boundaries`).
- Different filing agents produce structurally different HTML: Workiva
  output (COLB) uses zero `<p>` tags, div-only; other agents (WSBC) use
  `<p>` heavily. Paragraph-unit detection has to handle both
  (`chunk_html.py::_leaf_elements`).
- Some filers split a single word across adjacent inline `<span>` runs for
  styling reasons with no space between them ("RI"+"SK" for "RISK") — text
  extraction uses `get_text("")` not `get_text(" ")` for this reason.
- 8-K items use two-level decimal numbering ("Item 7.01"), not 10-K's
  simple/lettered format ("Item 1A") — the heading regex handles both.
- `pandas.read_html` needs **bytes**, not a decoded `str` — these filings
  declare an XML encoding, and lxml refuses to honor it on a Python `str`.
- Most `<table>` elements (140 in one real 10-K) are layout, not data —
  filtered by shape + numeric-cell-density. The Table of Contents itself is
  a real `<table>` that passes a naive numeric filter (page numbers count as
  "numeric") — excluded separately by detecting Item-heading-shaped rows.
- HTML colspan gets expanded by pandas into duplicated adjacent cells
  ("Oregon | Oregon | Oregon") — collapsed before serialization.

**Chart images**: of 894 total `<img>` tags across the corpus, only 11 are
genuine charts — the rest are logos, headshots, signatures, and proxy-voting
icons. The reliable signal is the **filename** containing "chart" or
"graph" (SEC filers' own naming convention), not `alt` text (95% of images
use `alt="graphic"` or `alt="LOGO"`, not discriminating). All 11 have real
Gemini Vision descriptions; 3 were personally viewed and verified against
the source image (100% accurate on chart type / trend direction / labels —
see `data/chart_eval_set.jsonl` for the grading notes).

**Section and document chunks were placeholders, and it mattered.** Phase
1 deliberately left document/section chunks holding only their heading
("Item 1A. Risk Factors"), deferring enrichment to Phase 4 — all 1,442
section chunks were verified to be heading-only. That is a false positive
factory: a chunk whose entire text is "Item 1A. Risk Factors" is a
near-perfect match for any risk question while containing nothing that
answers one, and it was observed as the top-scoring dense hit for "What are
the risks of the merger with Umpqua?" on a 500-chunk test index. The
original plan (LLM-generated summaries) is arithmetically impossible here —
1,944 chunks against a verified 20-requests/day Gemini quota is 97 days —
so `index/enrich.py` rolls a section's own opening paragraphs up into it
instead: free, deterministic, CI-reproducible, and it embeds the filing's
real language rather than a paraphrase. Sections that still come out empty
(e.g. a 10-Q "Item 3. Defaults Upon Senior Securities" whose body is
"None.") are flagged and **not indexed at all**. Enrichment never
recomputes `chunk_id` — ids are content-addressed over text, so
regenerating one would silently break every `parent_chunk_id` pointing at
it.

**Embedding throughput is CPU-contention-sensitive, and `ps` lies about
it.** Measured on this Mac: MPS embeds 256 chunks in a rock-steady 2.1s
across 15 consecutive iterations (zero drift); the same work on CPU takes
~11s. Two indexing runs appeared to "degrade" from ~90/s to ~20/s, and both
degradation windows coincided exactly with other corpus-loading Python
scripts being run alongside them — the degraded batches cost ~12s, i.e.
CPU-only speed. There is no leak or accumulating bug; the pipeline just
needs the machine to itself. Diagnosis was initially misdirected by `ps`
showing the process at 2.7% CPU, which looked like blocking on OpenSearch —
**MPS work executes on the GPU and does not register as process CPU time**,
so low CPU% does not mean idle. `scripts/build_index.py` now logs embed and
bulk seconds separately per batch so this is readable straight off the log.

**10-Q tables of contents leaked into the table corpus — FIXED.** 53 of
8,740 table chunks (0.6%, mostly SSB/COLB 10-Qs) were TOC tables.
`chunk_tables.py`'s `_ITEM_HEADING_CELL_RE` required whitespace *after* the
item number, which matches a 10-K's "Item 1A. Risk Factors" in one cell but
never a 10-Q's, where the number sits alone in its own column as exactly
"Item 1.". Fixed by anchoring with `(?:\s|$)`, and by scoring the exclusion
per *row* rather than per cell — in a 10-Q TOC the "Item N." cells are only
~14% of cells, diluted below any threshold real financial tables survive.

Verified end to end on 2026-08-16: 8,671 table chunks on disk and 8,671 in
the live index, **0 TOC-shaped by the current rule**, and indexed chunk-type
counts sum to exactly the 38,483 documented below. Regression tests cover
the 10-K shape, the 10-Q "Item 1." shape, and a real GBCI en-dash variant
(`tests/test_chunk_tables.py::TestTableOfContentsExclusion`). No further
ingestion or re-index is needed — a stale version of this note previously
said otherwise and caused a ticket to be opened for work already done.

**SEC's `fy`/`fp` fields identify the filing, not the fact — this produced
wrong answers.** Columbia's FY2023 10-K reports 2021, 2022 and 2023 net
income as prior-year comparatives, and all three carry `fy=2023, fp=FY`.
`chunk_xbrl.py`'s period label fell back to `FY{fy}{fp}` when SEC assigned
no normalized `frame`, so all three were indistinguishable: two facts
collided on an identical content-addressed `fact_id`, and a lookup keyed on
the label returned **$336.8M** (the 2022 comparative) for a 2023 question
against a verified $348.7M. Glacier was worse — six values shared the label,
including individual quarters, returning $303.2M against a verified $222.9M.
Fixed by capturing `period_start`/`period_end` on every `StructuredFact`
(and including them in the fingerprint) and selecting on actual dates:
durations must start and end inside the year and span 350–380 days;
instants must fall on the year end.

**A later filing is not automatically a better source.** The same 2023
period also appears as a rounded `349,000,000` in a 2026 filing — which is
the value SEC promotes into its normalized `CY2023` frame. Preferring the
most recent filing therefore fails the hand-verified ground truth.
`structured_lookup.py` prefers the *earliest* accession (the original
as-filed figure) and surfaces the accession number so a user can see which
filing a number came from. Stated trade-off: a genuine restatement would
also be filed later, and this rule returns the superseded original.

**XBRL extraction is verified accurate**: 3 extracted facts (COLB net
income $348.7M, COLB deposits $41.6B, GBCI net income $223M, all FY2023)
were cross-checked against independent prose in the *same filings*' MD&A
sections — exact matches. See `results/extraction/report.json`.

---

## Status by phase

| Phase | State |
|---|---|
| 0 Scaffolding + EDGAR fetch | **Done** — 502 real filings, 5 companies, real manifest with accession numbers |
| 1 Hierarchical narrative chunking | **Done** — 30,088 chunks (502 document, 1,442 section, 28,144 paragraph) |
| 2 Table + XBRL structured extraction | **Done** — 8,740 tables, 10,416 XBRL facts, extraction eval 3/3 (100%) |
| 3 Chart/image understanding | **Done** — 11/11 real charts described, qualitative eval 3/3 (100%) |
| 4 Embeddings + baseline retrieval eval | **Done** — 38,483 chunks indexed; eval set awaiting user verification |
| 5 Hybrid search, reranking, chunking ablation | **Done** — RRF + cross-encoder, recall@10 0.703 (+0.099); 3 ablations |
| 6 Structured-vs-semantic query routing | **Done** — deterministic router, structured exactness 3/3 |
| 7 Generation + groundedness evaluation | **Code done, no numbers** — Gemini daily quota exhausted; harness is resumable |
| 8 FastAPI serving layer | **Done** — /ask, /search, /route, /healthz, /readyz, /metrics |
| 9 Docker + local OpenSearch | **Done** — compose (OpenSearch + api profile), two-stage Dockerfile |
| 10 Kubernetes + observability | **Done** — StatefulSet/Deployment/HPA + Prometheus metrics |
| 11 CI/CD | **Done and verified green on GitHub** — all five jobs pass on `main` |
| 12 Terraform + real AWS OpenSearch demo (money-gated) | **Written + validated, never applied** — see terraform/README.md |
| 13 README + claim-to-artifact mapping | **Done** — README.md |

209 tests pass; `ruff check` clean.

### Retrieval numbers (real, from `results/retrieval/report.json`)

101 questions, 38,483 indexed chunks, **70 human-verified**. The table below
predates that verification — it was produced at 0 verified and has not been
re-run. Re-run before quoting these numbers anywhere:

| retriever | recall@1 | recall@5 | recall@10 | MRR | nDCG@10 | ms |
|---|---|---|---|---|---|---|
| dense (bge-small-en-v1.5 k-NN) | 0.149 | 0.257 | 0.322 | 0.201 | 0.228 | 13 |
| BM25 | 0.282 | 0.500 | 0.604 | 0.400 | 0.442 | 10 |
| hybrid (RRF, dense weight 0.25) | 0.218 | 0.465 | 0.663 | 0.360 | 0.425 | 28 |
| **hybrid + cross-encoder rerank** | **0.302** | **0.579** | **0.703** | **0.435** | **0.493** | 337 |

**Ablations** (`results/ablations/report.json`):
- *Fusion weight*: equal weighting is harmful (recall@1 0.183 vs BM25's
  0.282) — the weaker dense retriever pollutes the top ranks. 0.25 is best
  for recall@10 (0.663). **Tuned on the same eval set it is scored against,
  so that figure is optimistically biased.**
- *Chunk levels*: on the 35 paragraph-ground-truth questions, searching
  paragraphs only is best (0.757); adding tables drops it to 0.729, adding
  document+section to 0.714. The hierarchy helps as context, hurts as a
  search pool. An earlier version of this ablation was invalid — it scored
  table-ground-truth queries against configs forbidden from returning
  tables, a measurement artifact, since fixed.
- *Rerank depth*: 50 candidates optimal; **100 is worse than 50** (0.703 vs
  0.713) at 70% more latency.

**BM25 beats dense on every metric, by roughly 2x.** Recall@10 by chunk
type shows where: tables dense 0.18 / BM25 0.43, paragraphs 0.39 / 0.74,
chart descriptions 0.80 / 1.00. Serialized financial tables are numeric
soup — bad for a 384-dim semantic embedding, fine for exact lexical
matching — while chart descriptions are natural prose and the one place
dense is competitive. Head-to-head: BM25-only wins 41 queries, dense-only
wins 4, both miss 23.

**Two confounds that must be stated with these numbers, not buried:**

1. **The questions were written by reading the chunks**, so they reuse the
   chunks' vocabulary — which structurally favors lexical matching. A user
   asking in their own words would not hand BM25 that advantage. The gap is
   real but is probably overstated by this eval set.
2. **Labels are incomplete, and it materially depresses both scores.**
   Spot-checked: for "What is the date of the merger agreement between
   Columbia and Umpqua?", dense's top three hits all correctly state
   October 11, 2021 and all scored as misses, because the label points at
   an exhibit-index table that answers the question *worse* than they do.
   Not every miss is like this — "How did PPP loans affect Columbia's
   deposit balances in 2020?" is a genuine failure for both retrievers —
   but enough are that these figures are a floor, not an estimate.

Both are why Phase 5's headline must be the **delta** on this fixed eval
set, not the absolute level.

---

## Remaining work (all phases built; these are the honest gaps)

1. **Generation numbers.** `python -m duediligence.eval.run_groundedness_eval
   --limit 15` — resumable, skips completed questions, 20 Gemini
   requests/day. `results/generation/report.json` currently records 0
   answers because the quota was exhausted on the day it was built. The
   generation-backend seam now allows a locally-served model to generate
   with no quota ceiling while Gemini judges independently, which is what
   makes a full 101-question pass possible (issues #3, #4).
2. **Terraform apply** — money-gated, never without explicit real-time
   go-ahead. `terraform/README.md` has the cost breakdown.

**Closed since this list was written** (do not re-open these as work):

- *Eval-set verification.* 70 of 101 retrieval entries are now human-verified.
  A follow-on pass to widen single-chunk labels into all co-valid chunks was
  scoped and then **explicitly ruled out of scope** (issue #5). Tooling for it
  is merged and unused: `scripts/draft_covalidity_review.py`,
  `scripts/apply_covalidity_review.py`, `data/eval_covalidity_review.md`.
  Consequence: labels stay a mean of 1.02 chunks/question, so reported recall
  is a **floor, not an estimate**, and every report must keep saying so.
- *A real green CI run.* CI has run on GitHub and passed **all five jobs** —
  lint/unit, integration against a real OpenSearch container, serving-image
  build and boot, kind-cluster manifest validation, and Terraform validate.
- *The 10-Q TOC leak.* Fixed, tested, re-ingested and re-indexed — see the
  established-findings entry above.

## Previous next step: finish Phase 4, then Phase 5

**Blocked on the user (can't be faked):** verify a sample of the eval set.
`data/eval_verification_sample.md` has 20 of the 101 questions laid out with
their labeled chunk and what each retriever actually returned — weighted
toward the cases where the label looks wrong (8 both-miss, 6 split, 6
both-hit). The workflow: read each, then edit `data/eval_set.jsonl` to set
`"verified": true`, correct `relevant_chunk_ids`, and fill
`verification_note`. Questions that turn out ambiguous or unanswerable
should get `"relevant_chunk_ids": []`, which drops them from scoring rather
than counting as permanent misses. Re-run
`python -m duediligence.eval.run_retrieval_eval` afterwards — the report
prints the human-verified count, so a self-graded eval set cannot quietly
be presented as a curated one.

Then Phase 5: hybrid BM25+dense fusion, cross-encoder reranking, and the
chunking ablation (`--chunk-types` on `build_index.py` already supports
indexing levels independently for it). The headline is the **delta** on the
fixed eval set, not the absolute level — see the two confounds recorded
above.

**Watch the memory ceiling in Phase 5.** The reranker
(`cross-encoder/ms-marco-MiniLM-L-6-v2`) is a bigger model than bge-small,
and this is an 8 GB machine that already swaps — see the embedding-
throughput finding above. Run indexing/eval with nothing else heavy on the
box, and reach for `build_index.py --resume --batch-size 64` rather than
re-running from scratch.

---

## Repo map

```
duediligence/
  config.py         typed config loader
  ingest/           schema.py (Chunk, StructuredFact — content-addressed ids)
                    edgar_client.py (fetch, rate-limited, honest User-Agent)
                    chunk_html.py (hierarchical narrative chunking)
                    chunk_tables.py (pandas.read_html extraction)
                    chunk_xbrl.py (structured financial facts)
                    chunk_charts.py (Gemini Vision chart understanding)
  eval/             run_extraction_eval.py · run_chart_eval.py
                    retrieval_metrics.py (recall@k, MRR, nDCG, MAP, hit-rate)
                    run_retrieval_eval.py (dense + BM25 baselines)
  index/            embed.py (bge-small-en-v1.5, query-prefix + normalization)
                    enrich.py (index-time rollup of placeholder doc/section chunks)
                    opensearch_client.py (two backends, mapping, k-NN + BM25)
                    hybrid_search.py (RRF fusion) · rerank.py (cross-encoder)
  route/            query_router.py (deterministic) · structured_lookup.py
  api/              app.py (FastAPI: /ask /search /route /healthz /readyz /metrics)
  generate/         gemini_client.py · backends.py (injected text-generation
                    backends; keeps the groundedness judge separable from
                    the generator) · answer.py
  track/            experiment.py (W&B run logging; no-op without a key)
config/config.yaml  companies, filing types, date range, EDGAR settings, model names
docker/             docker-compose.yml (local OpenSearch 2.19.1, k-NN enabled)
scripts/            fetch_filings.py · run_ingestion.py · run_chart_extraction.py
                    build_index.py (embed + index the corpus)
                    sample_eval_candidates.py · draft_eval_set.py (eval-set curation)
                    run_ablations.py (fusion weight, chunk levels, rerank depth)
                    draft_covalidity_review.py · apply_covalidity_review.py
                    (label-widening tooling — built, deliberately unused, see
                    the eval-set note under Remaining work)
data/
  manifest.json         real provenance: accession numbers per filing
  filings/<TICKER>/     downloaded HTML + companyfacts.json (large, gitignored)
  chunks/<TICKER>.jsonl        narrative chunks
  tables/<TICKER>.jsonl        table chunks + exact cell values
  facts/<TICKER>.jsonl         structured XBRL facts
  chunks_charts/<TICKER>.jsonl chart description chunks
  extraction_eval_set.jsonl    hand-verified XBRL ground truth (3 entries)
  chart_eval_set.jsonl         hand-graded chart description rubric (3 entries)
  eval_candidates.jsonl        163 stratified sampled chunks the eval questions were written from
  eval_set.jsonl               101 retrieval (question, relevant_chunk_ids) pairs
results/
  extraction/report.json   3/3 (100%)
  charts/report.json       3/3 (100%)
tests/              45 tests, one file per ingest/eval module
```

---

## Working style the user has asked for (same as PathFinder)

- Keep instructions to the user short and concrete.
- Do the code, IaC, tests, and docs yourself. Only ask the user for: eval-set
  curation/verification (can't be faked), API keys/credentials, and
  explicit go-ahead before anything that costs real money.
- When something breaks, diagnose the root cause rather than working around
  it — this project's whole value is the list of real bugs found by actually
  running things against real data (see "Established findings" above).
- Resume bullets are deferred — focus on project quality, metrics, and
  breadth. Bullets come later, at the end, and only when asked.
- Every retrieval/extraction claim needs a real report.json, not a vibe.

---

## Agent skills

### Issue tracker

Issues live in this repo's GitHub Issues (`Dayallenr/RAG`), managed with the
`gh` CLI. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: `CONTEXT.md` and `docs/adr/` at the repo root, both created
lazily — their absence is not a problem to flag. See `docs/agents/domain.md`.
