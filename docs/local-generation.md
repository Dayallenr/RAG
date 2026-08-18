# Why generation runs on a local GPU

This project runs across two machines, which is unusual enough to be worth
explaining rather than leaving a reader to wonder why half the scripts
assume a model that is not the hosted one.

- **A Mac (8 GB, Apple MPS).** Holds the OpenSearch index, the embeddings,
  the reranker, the API, and the hosted-model API key. Everything that
  retrieves or serves happens here.
- **A Windows PC (RTX 5070).** Runs `qwen3:8b` under Ollama. Its only job is
  generating text in bulk.

## The arithmetic that forces it

The hosted free tier allows **20 requests per day** on this key. That is not
a rate limit I read in documentation — it is a limit I found by getting a
429 after the twentieth call.

Against that ceiling:

| Job | Calls needed | Hosted | Local |
|---|---|---|---|
| Synthetic training queries | 4,776 | **239 days** | one sitting |
| Answers for the 101-question eval set | 89 | ~5 days | one sitting |

There is no version of this project where 4,776 generations happen on the
free tier. Paying for the calls was the other option; a GPU I already own
was the cheaper one. So the choice was not "local model versus hosted
model" on quality grounds — it was "local model versus not doing the work".

Only 89 of the 101 eval questions call a model at all. The other 12 route to
exact XBRL lookup, and their answer is already a precise figure with the
accession number that reported it. Restating an exact number through a
language model can only introduce error, so those pass through untouched.

## Why generation and judging use different models

The local model generates the answers; the hosted model judges them for
groundedness. That split is deliberate and it is the reason the groundedness
score means anything — a model grading its own output is self-assessment,
and self-assessment is not a measurement. Judging is 101 calls spread over
several days, which fits inside the free tier where generation does not.

## Git is the transport

The two machines are on different networks (the Mac on `10.0.0.x`, the PC on
`172.16.0.x`), so the Mac cannot reach the PC's Ollama server directly.

Rather than punch a hole between the networks or copy files by hand, the
repository is the channel: the PC clones, pulls its inputs, generates,
commits the output, and pushes; the Mac pulls the result and carries on.

This started as a workaround and turned out to be the better design. Every
artifact that crosses between machines is versioned, diffable, and
attributable to a commit — including the generated training data and the
generated answers, which are exactly the artifacts whose provenance a reader
should be able to check. Nothing arrives on the serving machine without a
commit explaining where it came from.

It also keeps the PC's dependency list to almost nothing. The generation
scripts pull in `requests` and no more — no torch, no
`sentence-transformers`, no OpenSearch client — which was verified rather
than assumed. Everything those scripts read (`data/chunks/`, `data/tables/`,
`data/eval_set.jsonl`) is tracked; the 762 MB of raw filings is not, and is
not needed.

## The guard that has to survive all of this

Training queries are generated from the same corpus the eval set is labelled
against. `duediligence/train/synthetic.py` excludes every chunk the eval set
labels, and drops generated queries too close to an eval question. Weakening
that threshold to keep more training data would convert the fine-tuning
result from a measurement of generalisation into a measurement of how well
the model memorised the test set.
