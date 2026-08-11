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
| Repo | `/Users/dayallenragunathan/CodingProjects/RAG` (no git remote yet, no commits yet — see Immediate next step) |
| Python | 3.13.5, venv at `.venv/` |
| Secrets | `.env` (gitignored) holds a **real, working** `GOOGLE_API_KEY`. `.env.example` is the tracked placeholder. |
| Gemini model | `gemini-flash-latest`, **not** a pinned version — `gemini-2.5-flash` was confirmed dead ("no longer available to new users") on this API key despite still appearing in the model list. The `-latest` alias tracks whatever Google currently recommends. |
| Gemini free tier quota | **20 requests/day** for the vision-capable flash model on this key (confirmed by an actual 429, not documentation) — not just a per-minute limit. Any script calling Gemini must be idempotent/resumable (see `scripts/run_chart_extraction.py`'s `skip_urls` pattern) or you'll burn the day's quota re-doing finished work. |
| AWS | User has ~$100 in credits, same budget pool as PathFinder. Zero-spend by default; real AWS OpenSearch Service only for one short, gated, explicitly-approved demo late in the project. |

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
| 4 Embeddings + baseline retrieval eval | **Not started ← next** |
| 5 Hybrid search, reranking, chunking ablation | Not started |
| 6 Structured-vs-semantic query routing | Not started |
| 7 Generation + groundedness evaluation | Not started |
| 8 FastAPI serving layer | Not started |
| 9 Docker + local OpenSearch | Not started |
| 10 Kubernetes + observability | Not started |
| 11 CI/CD (must verify a real green run on GitHub, not just local validation) | Not started |
| 12 Terraform + real AWS OpenSearch demo (money-gated) | Not started |
| 13 README + claim-to-artifact mapping | Not started |

45 tests pass; `ruff check` clean.

---

## Immediate next step: Phase 4

Two things need building before the retrieval eval can run at all, then the
eval itself:

1. **Local OpenSearch isn't running yet.** Nothing has stood up even a dev
   instance — Phase 4 needs somewhere to index into. Bring up OpenSearch via
   Docker (`docker run -p 9200:9200 -e "discovery.type=single-node" ...
   opensearchproject/opensearch:latest`, or write the `docker-compose.yml`
   Phase 9 was going to build anyway — pulling that piece forward makes
   sense) before writing the indexing/embedding pipeline.
2. **Embedding pipeline**: embed the ~39k text chunks (30,088 narrative +
   8,740 tables + 11 chart descriptions — XBRL facts stay structured, never
   embedded, per the routing design) with `BAAI/bge-small-en-v1.5`
   (self-hosted, `sentence-transformers`, already in `requirements.txt`),
   index into OpenSearch with k-NN enabled.
3. **Retrieval metrics**: implement recall@k, MRR, nDCG
   (`duediligence/eval/retrieval_metrics.py`, doesn't exist yet).
4. **Eval-set curation — needs the user, not just Claude Code.** Hand-curate
   ~100+ `(question, relevant_chunk_ids)` pairs by reading the actual
   filings. This is the labor-intensive, non-automatable part — the same
   discipline as PathFinder's KITTI eval set: a self-graded eval set is
   worthless, and the user needs to be able to defend specific examples in
   an interview. Suggested split from earlier in this project: Claude drafts
   candidate questions + identifies chunk_ids, user verifies/corrects a
   sample rather than writing all ~100 from scratch — but confirm this
   approach with the user again if it wasn't already settled.
5. Run the eval, produce `results/retrieval/report.json` with a real
   (probably mediocre) baseline number — that's the point, Phase 5's hybrid
   search + reranking is what improves it, and the delta is the headline
   finding (this project's version of PathFinder's "49 mAP points" result).

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
  generate/         gemini_client.py (shared client, text + vision)
  eval/             run_extraction_eval.py · run_chart_eval.py
                    (retrieval_metrics.py, run_retrieval_eval.py — Phase 4, not built yet)
  index/            (Phase 4 — not built yet: embed.py, opensearch_client.py, hybrid_search.py, rerank.py)
  route/            (Phase 6 — not built yet: query_router.py)
  api/              (Phase 8 — not built yet: FastAPI app)
config/config.yaml  companies, filing types, date range, EDGAR settings, model names
scripts/            fetch_filings.py · run_ingestion.py · run_chart_extraction.py
data/
  manifest.json         real provenance: accession numbers per filing
  filings/<TICKER>/     downloaded HTML + companyfacts.json (large, gitignored)
  chunks/<TICKER>.jsonl        narrative chunks
  tables/<TICKER>.jsonl        table chunks + exact cell values
  facts/<TICKER>.jsonl         structured XBRL facts
  chunks_charts/<TICKER>.jsonl chart description chunks
  extraction_eval_set.jsonl    hand-verified XBRL ground truth (3 entries)
  chart_eval_set.jsonl         hand-graded chart description rubric (3 entries)
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
