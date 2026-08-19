# 0005 — Reversing the decision not to fine-tune anything

**Status:** accepted, supersedes the original no-fine-tuning scope. Trained,
indexed and measured on 2026-08-18 — see *Outcome* at the end, which is the
part worth reading: the fine-tune worked and the served pipeline cannot see
it, for a reason in the fusion settings rather than in the model.

## Context

This project started with an explicit rule: embedding and reranker models
are self-hosted and **inference-only**. No fine-tuning, no training step.

That was a sound decision for the constraints at the time. The only machine
was an 8 GB Mac whose GPU is Apple MPS. Keeping everything inference-only
meant the whole pipeline ran on that one machine, in Docker, and in CI, with
no GPU dependency anywhere.

Two things then changed.

1. **The measurement got embarrassing for the dense retriever.** BM25 beats
   dense on every metric by roughly 2x — recall@10 0.604 against 0.322, and
   0.425 against 0.200 on table-ground-truth questions. Head to head at
   k=20, BM25 finds the labelled chunk and dense misses it on 40 questions;
   the reverse happens on 3. A general-purpose `bge-small-en-v1.5` has never
   seen the language of SEC filings. That is not a bug to fix by tuning
   fusion weights; it is a domain-adaptation gap, and adapting the encoder
   is the direct answer to it.

   Figures from `results/retrieval/report.json`, re-run against the eval set
   with **101 of 101** entries human-verified. The figures above originally
   came from a run made when **0** were verified; verification corrected no
   labels, so every quality metric reproduced bit-identically and these
   numbers stand as current rather than as merely motivating. Only the
   latencies moved, and for a reason unrelated to the labels (see ADR 0001).
2. **A CUDA machine became available** — a Windows PC with an RTX 5070. The
   GPU-independence constraint that made the original rule necessary stopped
   applying, because training can happen on a machine that is not the
   machine that serves.

## Decision

Fine-tune the bi-encoder on synthetic queries mined from the corpus, with
hard negatives mined from the *current* retriever's top hits. Training runs
on the RTX 5070.

Selecting the model and its matching index together is done by config
profile (`config/profiles/finetuned.yaml`), because a model and the index it
embedded must travel together: querying an index with a different model
scores cosine similarity across two incompatible spaces, which produces
plausible-looking rankings rather than an error. The loader refuses a profile
that changes one without the other, and refuses an unknown profile name
rather than silently falling back to the baseline.

The cross-encoder stays un-fine-tuned. Reopen that only if the bi-encoder
delta comes in weak.

## Alternatives considered

- **Keep the inference-only rule and tune retrieval instead** (fusion
  weights, rerank depth, chunk levels). Already done — that is the ablation
  sweep. It moved recall@10 from 0.604 to 0.703. Useful, and it does not
  touch the underlying reason dense retrieval is weak here.
- **Swap in a larger off-the-shelf embedding model.** Cheaper and it might
  well help. Rejected as the primary move because it does not produce a
  measurement: "a bigger model scores better" is not a result, whereas "the
  same architecture, adapted to this corpus, moves recall by X on a held-out
  split" is.
- **Fine-tune the cross-encoder first.** Rejected. The bi-encoder is the
  weaker component by a wide margin and it is the one that determines what
  the reranker ever gets to see.

## Consequences

**Accepted downside — the project is no longer single-machine.** Training
needs CUDA. Serving and indexing still run on the Mac, so the two machines
must exchange artifacts; git is the transport
(`../local-generation.md` explains why). Reproducing the training step now
requires hardware most readers of this repository do not have.

**Accepted downside — the claim rests on scripts and reports, not weights.**
No fine-tuned weights are published. What will be verifiable is the training
script, the tracked sample of the training data, the hosted training run, and
the report in `results/` — of which only the script and the tracked sample
exist today, because the run has not happened.

**Accepted risk — the delta might be small or negative.** That result gets
published either way. A fine-tune that fails to beat BM25 on this corpus is
a legitimate finding about numeric-heavy financial text, and reporting only
favourable outcomes would make every other number here worth less.

**Guard that had to come with it.** Training data is generated from the same
corpus the eval set is labelled against, so contamination is the obvious
failure mode. `duediligence/train/synthetic.py` drops any query whose source
passage is labelled in `data/eval_set.jsonl`, and drops generated queries
too similar to an eval question. Without that, the delta measures
memorisation of the test set.

## Outcome, measured 2026-08-18

The training run happened on the RTX 5070 (one epoch, 121 s,
`results/training/report.json`), the index was rebuilt from the checkpoint,
and the delta was measured as a four-run matrix — base and fine-tuned, each
with and without the cross-encoder — in `results/finetune_delta/report.json`.

**The decision was right about the bi-encoder and wrong about what it would
buy.** On the held-out test split dense recall@10 goes 0.367 → **0.600**,
reaching parity with BM25's 0.600, and it reproduces on every split (+0.233
test, +0.232 dev, +0.233 all). It lands where this ADR argued the domain gap
was: over all 101 questions, tables 0.200 → 0.550 and sections 0.350 → 0.650,
against paragraphs 0.414 → 0.457.

**The pipeline this repository serves does not move by a thousandth.** Through
`hybrid + cross-encoder rerank` every metric is unchanged on every split, and
the reranked result lists are byte-identical on all 101 questions. That is not
the reranker absorbing the gain — it is RRF's arithmetic. A document only
dense retrieval finds scores `0.25 / 61` at best, while BM25's document at
candidate depth `c` scores `1 / (60 + c)`, so no dense-only document can enter
the fused pool until `c > 184`; the pipeline runs at 50. Measured against the
live index (`scripts/verify_rerank_pool.py`): the fused pool equals BM25's
candidate set on 30/30 test questions in both arms. The fine-tuned vectors
reorder the reranker's input and never change its membership.

The "accepted risk" above anticipated a small or negative delta and committed
to publishing it. The actual result is stranger and more useful: a large,
reproducible gain in the component that was trained, and zero effect on the
system, for a reason that lives in the fusion configuration rather than in the
model. Realising it in the served pipeline is a fusion change — dense weight,
candidate depth past 184, or reranking a dense-sourced pool — and that is a
separate decision from this one, which is why it is not folded in here.

The second accepted downside is mostly closed. The checkpoint digest manifest
(`results/training/checkpoint.json`) is committed, and the weights that produced
these numbers match it — `model.safetensors` byte for byte — so the delta is an
attributable measurement of the trained model. What remains is narrow and
stated rather than smoothed over: `transfer_checkpoint.py verify` exits 1 on
`modules.json`, a 410-byte module list holding no weights, and the only file in
the checkpoint carrying a timestamp this machine could have written. The
[model card](../model-card.md#provenance-what-ties-these-weights-to-that-run)
records the evidence file by file.
