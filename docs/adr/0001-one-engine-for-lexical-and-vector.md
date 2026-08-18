# 0001 — One search engine serves both lexical and vector retrieval

**Status:** accepted

## Context

The retrieval path needs BM25 and approximate nearest-neighbour search over
the same 38,483 chunks, and it needs to fuse the two. The default modern
answer is a dedicated vector database (Pinecone, Weaviate, Qdrant) sitting
next to a separate lexical index.

## Decision

Use OpenSearch for both. Its k-NN plugin holds the 384-dimensional
embeddings; its standard analyzed text field serves BM25; a single index
holds both, and fusion happens over two queries against the same documents.

## Alternatives considered

- **A dedicated vector DB plus Elasticsearch/OpenSearch for lexical.**
  Rejected. Two stores means two ingestion paths, two consistency problems,
  and — the part that actually decided it — chunk ids that have to be kept
  in sync across systems for reciprocal-rank fusion to mean anything. Ids
  here are content-addressed hashes; a partial re-index of one store and not
  the other produces fusion over two different corpora, silently.
- **FAISS in-process plus BM25 in OpenSearch.** Rejected. FAISS would be
  fast and free, but it puts the index in the API process's memory on an
  8 GB machine that already swaps, and it has no story for the served,
  containerised, Kubernetes-deployed version of this project.

## Consequences

**Accepted downside, and it shows up in the numbers.** OpenSearch's k-NN is
not best-in-class. In the eval run (`results/retrieval/report.json`, 101 of
101 questions human-verified) the k-NN path averages **36 ms** per query at
k=20 against BM25's **18 ms** on the same index — so the vector side is the
slower of the two retrievers a dedicated store would most plausibly beat. It
is not the binding constraint: the full hybrid-plus-rerank path averages
**342 ms**, of which the cross-encoder is the clear majority. Sweeping the
ANN parameters into a recall-latency curve is tracked separately (#14) and
would tell us how much of the 36 ms is tuning rather than engine choice.

**Read the ratio, not the absolute figures.** An earlier run of the same
eval recorded 208 ms and 89 ms for the same two paths — 6x these numbers,
on the same code and the same index, because that run shared the machine
with other work (this is an 8 GB laptop that also hosts OpenSearch; see
`docs/engineering-notes.md` on CPU contention). The 2x k-NN-to-BM25 ratio
held across both runs, and it is the ratio this decision rests on.

**Second accepted downside.** It couples the two retrievers' availability:
when OpenSearch is down, neither works. With separate stores one path could
degrade gracefully. For a due-diligence tool that fuses both by default,
half a retriever is not a useful product, so this costs little in practice.

**Benefit that decided it.** One ingestion path, one set of ids, one thing
to run in Docker, in CI, and in Kubernetes — and one managed service (AWS
OpenSearch Service) for the cloud demo instead of two.
