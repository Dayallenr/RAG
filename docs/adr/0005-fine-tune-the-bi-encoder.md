# 0005 — Reversing the decision not to fine-tune anything

**Status:** accepted, supersedes the original no-fine-tuning scope

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

   Figures from `results/retrieval/report.json`. That report was produced
   when **0** of the 101 eval entries were human-verified; 70 are verified
   now, and it has not been re-run since. Treat these as the numbers that
   motivated the decision, not as current.
2. **A CUDA machine became available** — a Windows PC with an RTX 5070. The
   GPU-independence constraint that made the original rule necessary stopped
   applying, because training can happen on a machine that is not the
   machine that serves.

## Decision

Fine-tune the bi-encoder on synthetic queries mined from the corpus, with
hard negatives mined from the *current* retriever's top hits. Training runs
on the RTX 5070.

Selecting the model and its matching index together by config profile is
**planned and not yet built** (#20) — today `config.models.embedding_model`
is a single name, so swapping models means editing config rather than
choosing a profile. The point of that ticket is that a model and the index
it embedded must travel together; mixing them silently produces garbage
scores.

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
No fine-tuned weights are published. What is verifiable is the training
script, the tracked sample of the training data, the hosted training run,
and the report in `results/`.

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
