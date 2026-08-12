# Bank M&A Due-Diligence RAG

A retrieval-augmented question-answering system over **real SEC EDGAR
filings**, built around Columbia Banking System's 2023 merger of equals with
Umpqua Holdings — a real, public, independently fact-checkable transaction —
plus three more regional banks (Glacier Bancorp, WesBanco, South State) for
corpus breadth and cross-company comparison.

**502 real filings. 38,552 indexed chunks. No synthetic data.**

Factual questions ("What was Columbia's net income for 2023?") route to an
exact XBRL lookup and return a figure traceable to the accession number that
reported it. Narrative questions ("What are the risks of the Umpqua
merger?") route to hybrid search with cross-encoder reranking and cited
generation.

---

## Every claim below maps to an artifact you can re-run

This project's rule is that no number appears in this README unless a script
produced it and a report file records it. Where something is unverified,
partial, or a lower bound, it says so.

| Claim | Artifact | How to reproduce |
|---|---|---|
| 502 filings, 5 companies, real accession numbers | `data/manifest.json` | `python scripts/fetch_filings.py` |
| 30,088 narrative chunks (502 doc / 1,442 section / 28,144 paragraph) | `data/chunks/*.jsonl` | `python scripts/run_ingestion.py` |
| 8,740 table chunks with exact cell values | `data/tables/*.jsonl` | same |
| 10,416 XBRL structured facts | `data/facts/*.jsonl` | same |
| 11 chart descriptions (Gemini Vision) | `data/chunks_charts/*.jsonl` | `python scripts/run_chart_extraction.py` |
| XBRL extraction accuracy **3/3 (100%)** | `results/extraction/report.json` | `python -m duediligence.eval.run_extraction_eval` |
| Chart understanding **3/3** hand-graded | `results/charts/report.json` | `python -m duediligence.eval.run_chart_eval` |
| Retrieval: dense / BM25 / hybrid / +rerank | `results/retrieval/report.json` | `python -m duediligence.eval.run_retrieval_eval` |
| Fusion-weight, chunk-level, rerank-depth ablations | `results/ablations/report.json` | `python scripts/run_ablations.py` |
| Routing + structured exactness **3/3** | `results/routing/report.json` | `python -m duediligence.eval.run_routing_eval` |
| 161 passing tests, ruff clean | — | `pytest -q && ruff check .` |

---

## Headline result: reranking, not embeddings

Measured on 101 questions against the full 38,552-chunk index.

| retriever | recall@1 | recall@5 | recall@10 | MRR | nDCG@10 | ms/query |
|---|---|---|---|---|---|---|
| dense (bge-small-en-v1.5) | 0.149 | 0.257 | 0.322 | 0.201 | 0.228 | 13 |
| BM25 | 0.282 | 0.500 | 0.604 | 0.400 | 0.442 | 10 |
| hybrid (RRF) | 0.218 | 0.465 | 0.663 | 0.360 | 0.425 | 28 |
| **hybrid + cross-encoder rerank** | **0.302** | **0.579** | **0.703** | **0.435** | **0.493** | 337 |

**+0.099 recall@10 over the strongest single retriever**, at 27x the
latency.

Three findings worth more than the headline number:

**1. Dense retrieval lost badly to BM25 here — 0.322 vs 0.604 recall@10.**
Not the expected result, and the breakdown says why: on serialized financial
tables dense scores 0.17 against BM25's 0.42. A 384-dimensional semantic
embedding of a table that reads `Balance at January 1, 2019 | 73249 | $ |
1642246 | ...` carries little signal, while exact lexical matching handles
it. Dense is only competitive on chart descriptions (0.80), which are the
one part of the corpus written as natural prose.

**2. Naive RRF fusion made things worse, and the ablation shows the fix.**
Equal-weight fusion scored *below* BM25 alone on precision (recall@1 0.183
vs 0.282). Sweeping the dense weight from 0 to 1 (`results/ablations`)
showed why — the weaker retriever pollutes the top ranks — and that 0.25 is
the best setting, recovering recall@10 0.663.

**3. The chunk hierarchy helps as context but hurts as a search pool.** On
the 35 questions whose answer is a paragraph, restricting search to
paragraphs only scores best (recall@10 0.757); adding table chunks drops it
to 0.729, and adding document and section chunks drops it to 0.714. Every
extra level is a distractor. This is what motivates the router.

Reranking depth was also swept: 50 candidates is optimal, and **100 is
worse than 50** (0.703 vs 0.713) while costing 70% more latency — a deeper
pool gives the cross-encoder more chances to promote a distractor.

### Two caveats that belong next to those numbers

- **The absolute values are a lower bound.** Relevance labels come from a
  stratified sample of 163 chunks, not exhaustive judgments over all 38,552.
  Verified by inspection: for *"What is the date of the merger agreement
  between Columbia and Umpqua?"*, the dense retriever's top three hits all
  correctly state October 11, 2021 — and all scored as misses, because the
  label points at an exhibit-index table that answers the question worse.
- **The questions were written by reading the labelled chunks**, so they
  share vocabulary with them, which structurally favours lexical matching.
  The dense-vs-BM25 gap is real but is probably overstated by this eval set.

Comparisons *between* retrievers on this fixed set remain sound, which is
why the reranking delta is the headline rather than the absolute level.

---

## Structured routing: the exact-answer path

A deterministic rule set — not an LLM call — decides whether a question is a
lookup or a search. An LLM router would add an unpredictable failure surface
in front of a system whose selling point is traceability, cost a request
against a 20/day quota, and resist unit testing.

```
$ curl "localhost:8000/route?question=What was Columbia's net income for 2023?"
{"route": "structured", "concept": "NetIncomeLoss", "company": "COLB",
 "fiscal_year": 2023,
 "reasons": ["matched XBRL concept NetIncomeLoss via 'net income'",
             "identified company COLB", "identified fiscal year 2023",
             "concept + company + period form a complete lookup key"]}
```

A structured route requires **all three** of concept, company and period.
"What was net income?" names a concept but no company or year — there is no
row to fetch, so it falls back to search rather than guessing which of five
banks was meant. Narrative markers ("why", "explain", "compare") veto a
structured route even when the key is complete.

**Structured exactness: 3/3** against `data/extraction_eval_set.jsonl`,
whose values were verified by hand against the filings' own MD&A prose. This
is the only eval in the project with an unambiguous right answer.

The routing *classification* score (36/36) is reported in
`results/routing/report.json` but is explicitly labelled a regression test,
not evidence: the rules and the test cases share an author.

---

## Architecture

```
SEC EDGAR ──► ingest ──► 4 extraction paths        ──► OpenSearch (BM25 + k-NN)
                          ├─ narrative HTML (doc→section→paragraph)
                          ├─ tables (pandas.read_html + exact cells)
                          ├─ XBRL facts ─────────────► exact lookup (not embedded)
                          └─ chart images (Gemini Vision)

query ──► router ──┬── STRUCTURED: XBRL lookup ──► figure + accession number
                   └── SEMANTIC:   hybrid RRF ──► rerank ──► cited generation
```

XBRL facts are deliberately **never embedded**. `NetIncomeLoss = 348715000
USD CY2023` has no useful semantic neighbourhood; it is answered by lookup.

| Component | Choice | Why |
|---|---|---|
| Store | OpenSearch 2.19.1 | One engine for BM25 *and* k-NN — hybrid search is one query, not a cross-system fan-out |
| Embeddings | `BAAI/bge-small-en-v1.5` (384d) | Self-hosted, inference-only, small enough to embed 38k chunks on a laptop |
| Reranker | `ms-marco-MiniLM-L-6-v2` | Cross-encoder over 50 candidates; the single biggest quality win |
| Generation | Gemini free tier | Multimodal (also drives chart understanding), no card required |
| API | FastAPI | Deliberately different from this author's other project's gRPC stack |

---

## Running it

```bash
docker compose -f docker/docker-compose.yml up -d      # OpenSearch
python scripts/build_index.py --recreate               # embed + index (~10 min)
python -m duediligence.eval.run_retrieval_eval         # reproduce the table above
```

Serve the API:

```bash
docker compose -f docker/docker-compose.yml --profile api up -d
curl -X POST localhost:8000/ask -H 'content-type: application/json' \
  -d '{"question": "What are the risks of the Umpqua merger?"}'
```

`/healthz` is liveness and never touches OpenSearch — a search blip must not
trigger pod restarts. `/readyz` is readiness and does check it. `/metrics`
exposes Prometheus counters, including the structured-vs-semantic split.

Kubernetes manifests are in `k8s/` (OpenSearch as a StatefulSet, API as a
Deployment with an HPA). Terraform for AWS OpenSearch Service is in
`terraform/`.

---

## Honest status

**Complete and verified by running it:** ingestion, chunking, table and XBRL
extraction, chart understanding, embeddings and indexing, retrieval eval,
hybrid search, reranking, three ablations, query routing, structured lookup,
and the FastAPI service — the API was run against the live index and every
endpoint exercised (`/healthz`, `/readyz`, `/route`, `/ask` on both routes,
`/search` with filters, `/metrics`, and request validation).

**Written but not executed:**

- **The Docker image has never been built.** The Dockerfile is written, and
  `docker compose config` validates, but Docker Hub pulls timed out
  repeatedly in this environment, so the build was never completed. CI's
  `docker-build` job will be the first real test of it.
- **The Kubernetes manifests parse but were not schema-validated.** They
  load as valid YAML with the expected kinds; `kubectl --dry-run=server`
  needs a running cluster and none was available. CI's `manifests` job does
  this against a kind cluster.

**Not yet verified, and stated as such:**

- **The 101-question retrieval eval set is Claude-drafted and unverified.**
  Every entry carries `"verified": false`, and every report prints the
  human-verified count (currently 0). `data/eval_verification_sample.md`
  lays out 20 of them for review, weighted toward cases where the label
  looks wrong.
- **Generation and groundedness have no numbers yet.** The pipeline runs end
  to end, the citation-validation logic is unit-tested, and the eval harness
  is written and resumable — but the Gemini free tier allows 20 requests per
  day and the day's quota was exhausted. `results/generation/report.json`
  currently records 0 answers. Re-running continues where it left off.
- **Terraform has never been applied.** It passes `fmt` and `validate`, and
  CI enforces both, but no AWS resource has been created. Validation proves
  the configuration is well-formed and nothing more. See
  `terraform/README.md` for the cost breakdown and why it is gated.
- **CI has not yet run on GitHub.** The workflow is written; this repository
  has no remote, so no green run exists to point at.

**Known defect, measured and not yet fixed:** 53 of 8,740 table chunks
(0.6%) are 10-Q tables of contents. The exclusion regex requires whitespace
after the item number, which matches a 10-K's `Item 1A. Risk Factors` in one
cell but never a 10-Q's, where the number sits alone as `Item 1.`.

---

## Things that broke, and what they taught

The value of running this against real data rather than a clean dataset is
the list of things that were wrong:

- **SEC's `fy`/`fp` fields describe the filing, not the fact.** Columbia's
  FY2023 10-K reports 2021, 2022 *and* 2023 net income as comparatives, all
  tagged `fy=2023, fp=FY`. Selecting on that label returned **$336.8M** (the
  2022 figure) for a 2023 question against a verified $348.7M. Only
  `start`/`end` dates disambiguate them — and two facts were colliding on an
  identical content-addressed ID as a result.
- **A later filing is not a better source.** The same period appears rounded
  to $349,000,000 in a 2026 filing — which is also the value SEC promotes
  into its normalized `CY2023` frame. The original as-filed figure is the
  traceable one.
- **Section chunks were empty.** All 1,442 held only their heading. A chunk
  whose entire text is `"Item 1A. Risk Factors"` was the top-scoring dense
  hit for a merger-risk query while containing nothing that answers it.
- **8 GB of RAM is a real constraint.** Indexing appeared to "degrade" from
  90/s to 20/s across two runs. It was not a leak: the JVM, Docker's VM and
  a resident torch model don't fit, and the machine swapped. Diagnosis was
  misdirected by `ps` showing 2.7% CPU — **MPS work runs on the GPU and does
  not register as process CPU time**, so low CPU% does not mean blocked.
- **Terraform caught its own dependency cycle.** The domain's access policy
  needed the domain's ARN while the domain needed the rendered policy;
  `validate` refused it, and the fix was a separate policy resource.

Earlier findings — the table of contents duplicating every heading, filers
splitting words across `<span>` runs, `pandas.read_html` requiring bytes not
`str`, 140 layout tables per 10-K, and only 11 genuine charts among 894
`<img>` tags — are documented in `CLAUDE.md`.
