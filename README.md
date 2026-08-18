# Bank M&A Due-Diligence RAG

A retrieval-augmented question-answering system over **real SEC EDGAR
filings**, built around Columbia Banking System's 2023 merger of equals with
Umpqua Holdings — a real, public, independently fact-checkable transaction —
plus three more regional banks (Glacier Bancorp, WesBanco, South State) for
corpus breadth and cross-company comparison.

**502 real filings. 38,483 indexed chunks. No synthetic data.**

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
| 8,671 table chunks with exact cell values (69 tables of contents excluded) | `data/tables/*.jsonl` | same |
| 10,416 XBRL structured facts | `data/facts/*.jsonl` | same |
| 11 chart descriptions (Gemini Vision) | `data/chunks_charts/*.jsonl` | `python scripts/run_chart_extraction.py` |
| XBRL extraction accuracy **3/3 (100%)** | `results/extraction/report.json` | `python -m duediligence.eval.run_extraction_eval` |
| Chart understanding **3/3** hand-graded | `results/charts/report.json` | `python -m duediligence.eval.run_chart_eval` |
| Retrieval: dense / BM25 / hybrid / +rerank | `results/retrieval/report.json` | `python -m duediligence.eval.run_retrieval_eval` |
| Fusion-weight, chunk-level, rerank-depth ablations | `results/ablations/report.json` | `python scripts/run_ablations.py` |
| Routing + structured exactness **3/3** | `results/routing/report.json` | `python -m duediligence.eval.run_routing_eval` |
| Kubernetes deployment, probes, Service routing | `results/deployment/k8s_verification.json` | `kind create cluster && kubectl apply -f k8s/` |
| 317 passing tests, ruff clean | — | `pytest -q && ruff check .` |

### What is *not* on that list, and why that matters

Everything above was produced by running the thing and is backed by a file
you can open. Two parts of this project are **not** on that list, and the
distinction is deliberate — reading code is not evidence that the code was
ever executed:

- **The AWS infrastructure has never been applied.** `terraform/` defines an
  OpenSearch domain and, behind an opt-in flag, a VPC/EKS/ECR stack. It
  passes `fmt` and `validate`, and CI enforces both — but validation proves
  the configuration is well-formed and nothing more. No AWS resource has
  ever been created from it, and the SigV4 signing path it would exercise in
  `duediligence/index/opensearch_client.py` has never run against a real
  domain.
- **Groundedness is measured on 9 of 101 answers.** All 101 answers are
  generated and recorded, but each independent judgment costs a request
  against a 20/day Gemini quota, so `results/generation/report.json` reports
  a claim-support rate over 9 judgments — real, and too few to quote as a
  system-level number.

If either of those later becomes verified, it gets an artifact in the table
above and a line here — not a quiet edit to a sentence elsewhere. That has
already happened once: the evaluation set used to be listed here as
unverified, and it now has an artifact instead (see below).

---

## Headline result: reranking, not embeddings

Measured on 101 questions against the full 38,483-chunk index. All 101 are
human-verified, and every eval report prints that count so a self-graded set
cannot be mistaken for a curated one.

| retriever | recall@1 | recall@5 | recall@10 | MRR | nDCG@10 |
|---|---|---|---|---|---|
| dense (bge-small-en-v1.5) | 0.158 | 0.277 | 0.322 | 0.208 | 0.233 |
| BM25 | 0.282 | 0.500 | 0.604 | 0.399 | 0.441 |
| hybrid (RRF, dense weight 0.25) | 0.218 | 0.485 | 0.663 | 0.361 | 0.424 |
| **hybrid + cross-encoder rerank** | **0.302** | **0.579** | **0.703** | **0.435** | **0.493** |

**+0.099 recall@10 over the strongest single retriever**, at 19x the
latency (342 ms against BM25's 18 ms). Latencies in
`results/retrieval/report.json` are machine-dependent — this is an 8 GB
laptop also running OpenSearch, and an earlier run of the identical code
recorded figures 6x higher because it shared the machine with other work —
so treat their ratios rather than their absolute values as meaningful.

Three findings worth more than the headline number:

**1. Dense retrieval lost badly to BM25 here — 0.322 vs 0.604 recall@10.**
Not the expected result, and the breakdown says why: on serialized financial
tables dense scores 0.20 against BM25's 0.42. A 384-dimensional semantic
embedding of a table that reads `Balance at January 1, 2019 | 73249 | $ |
1642246 | ...` carries little signal, while exact lexical matching handles
it. Dense is only competitive on chart descriptions (0.60 here, 1.00 for BM25), which are the
one part of the corpus written as natural prose.

**2. Naive RRF fusion made things worse, and the ablation shows the fix.**
Equal-weight fusion scored *below* BM25 alone on precision (recall@1 0.183
vs 0.282). Sweeping the dense weight from 0 to 1 (`results/ablations`)
showed why — the weaker retriever pollutes the top ranks — and that 0.25 is
the best setting, recovering recall@10 0.663.

**3. The chunk hierarchy helps as context but crowds the top ranks.** On
the 35 questions whose answer is a paragraph, restricting the searchable
pool to paragraphs only moves recall@1 from 0.314 to **0.400** and nDCG@10
from 0.570 to **0.612** against searching every level. It costs a little
recall@10 — 0.829 to 0.814, one question — so the other levels are not
useless; they occasionally carry the answer. But they are distractors where
it matters most, at the top of the ranking. This is what motivates the
router.

Reranking depth was also swept, and returns stop early: recall@10 peaks at
**25** candidates (0.713), and 100 is worse than both 25 and 50 (0.693) at
**604 ms** against 222 ms. A deeper pool gives the cross-encoder more
chances to promote a distractor. The configured depth of 50 sits between
them deliberately — it buys back the precision that depth 25 gives up
(recall@1 0.302 against 0.292) at the same nDCG@10.

### Two caveats that belong next to those numbers

- **The absolute values are a lower bound.** Relevance labels come from a
  stratified sample of 163 chunks, not exhaustive judgments over all 38,483.
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
Deployment with an HPA) — **verified by deploying to a real cluster**, see
`results/deployment/k8s_verification.json`.

Terraform for AWS (OpenSearch domain; optionally VPC + EKS + ECR) is in
`terraform/`. **It has never been applied — no AWS resource has ever been
created from it.** It passes `fmt` and `validate` and CI enforces both, but
that proves only that the configuration is well-formed. It does not prove
the domain comes up, that the k-NN plugin behaves the same on AWS's managed
build, or that the SigV4 signing path in `opensearch_client.py` works —
that code has never run against a real domain. Treat it as reviewed
infrastructure code, not as a deployment.

---

## Honest status

**Complete and verified by running it:** ingestion, chunking, table and XBRL
extraction, chart understanding, embeddings and indexing, retrieval eval,
hybrid search, reranking, three ablations, query routing, structured lookup,
and the FastAPI service — the API was run against the live index and every
endpoint exercised (`/healthz`, `/readyz`, `/route`, `/ask` on both routes,
`/search` with filters, `/metrics`, and request validation).

**Container and Kubernetes deployment: verified by deploying it.**
`results/deployment/k8s_verification.json` records the run. The image builds
(2.13 GB) and runs as non-root `appuser`; the full stack was deployed to a
kind cluster, the StatefulSet's PVC bound, and both API replicas plus
OpenSearch reached Ready. The probe design was confirmed under real
conditions rather than asserted: while OpenSearch was still starting,
`/healthz` stayed 200 and `/readyz` returned 503, so pods were held out of
the Service without being restarted — and both flipped to Ready the moment
the index existed. Traffic through the Service reached `/healthz`,
`/readyz`, `/route` and `/metrics`.

One real limitation found this way: the HPA reports
`FailedGetResourceMetric` on kind, which ships without `metrics-server`. The
manifest is correct; `metrics-server` is a cluster prerequisite. The HPA was
observed working in one respect — it immediately restored `minReplicas: 2`
after a manual scale to 1.

The in-cluster OpenSearch held an empty index, so this validated deployment,
probes and routing — not retrieval quality in-cluster.

**Since verified, and recorded rather than quietly edited:**

- **The 101-question retrieval eval set was drafted mechanically, then
  verified by hand.** All 101 entries now carry `"verified": true`, and
  every report prints that count. Verification corrected **no** labels, so
  the re-run reproduced every quality metric bit-identically — which is the
  evidence that the earlier figures were not a self-grading artifact. Two
  limits survive verification and are stated with every number: labels
  average 1.02 chunks per question, so recall is a **floor, not an
  estimate**, and the questions were written by reading the chunks they are
  labelled against, which favours lexical matching.

**Not yet verified, and stated as such:**

- **Groundedness is judged on 9 of 101 answers.** All 101 answers are
  generated and recorded (`results/generation/answers.jsonl`), but judging
  them costs a request against a 20/day Gemini quota, so
  `results/generation/report.json` reports a claim-support rate over **9**
  judgments — too few to quote as a system-level number. The harness is
  resumable and continues where it left off.
- **Terraform has never been applied.** It passes `fmt` and `validate`, and
  CI enforces both, but no AWS resource has been created. Validation proves
  the configuration is well-formed and nothing more. See
  `terraform/README.md` for the cost breakdown and why it is gated.

**Previously-known defect, now fixed:** 69 of 8,740 table chunks were 10-Q
tables of contents. Two things were wrong — the exclusion regex required
whitespace after the item number (never present in a 10-Q, where the cell is
exactly `Item 1.`), and the threshold counted *cells*, which a table of
contents dilutes to ~14% with its title and page-number cells. Measuring
both populations across all 8,740 tables showed a row-based signal separates
them cleanly: genuine tables sit at 0.000 even at the 99th percentile, every
table of contents at 0.268+. The corpus is now 8,671 tables.

**What removing them was worth, measured — and it is small.** Running the
retrieval eval either side of the re-ingestion isolates the effect, and the
honest answer is that 69 chunks out of 38,483 move the top ranks a little
and the deeper ranks not at all. Dense recall@5 goes 0.257 → 0.277 and
recall@1 0.149 → 0.158 (one question of 101); MRR and nDCG@10 rise by
0.007 and 0.005. BM25's recall is unchanged at every k (its MRR and nDCG@10
slip by 0.0002), every retriever's recall@10 is unchanged, and the reranked
figures are unchanged. By chunk type the one visible move is hybrid on paragraph questions,
0.800 → 0.829, against hybrid on table questions going the other way,
0.450 → 0.425.

That is the expected shape rather than a disappointment: a table of contents
is lexically stuffed with the section headings a narrative question uses, so
it competes for the *top* ranks it can least answer — which is where dense
retrieval and MRR moved — while a retriever that was going to find the right
chunk by rank 10 still does. The defect was worth fixing because the corpus
is wrong with it in, not because it was costing recall.

These figures come from runs either side of the re-ingestion commit rather
than from two live indices A/B'd against each other, so read them as a
before-and-after, not a controlled experiment. The ablation report was also
stale against this fix — it had never been re-run — and its all-levels
configuration did not reproduce the contemporaneous retrieval eval on
identical settings. It has been re-run; the two now agree exactly (0.8286),
and finding 3 above is stated from the re-run.

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
`<img>` tags — are documented in
[`docs/engineering-notes.md`](docs/engineering-notes.md).
