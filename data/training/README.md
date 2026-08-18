# Training data

Fine-tuning triplets for the bi-encoder, built from the corpus in three steps.

| File | What it is |
|---|---|
| `synthetic_queries.jsonl` | Generated queries, one per sampled passage. The input the splits are derived from. |
| `train.jsonl` | 12,758 mined `(query, positive, hard negative)` triplets. |
| `val.jsonl` | 1,429 more, held out by query so no query straddles the split. |

## All three are tracked, deliberately

An earlier version of this file kept the two splits out of git as
"deterministic output of a script whose inputs are tracked". Both halves of
that turned out to be wrong, and the cost was overstated:

- **They are not rebuildable from tracked inputs.**
  `scripts/mine_hard_negatives.py` mines negatives by running the *current*
  retriever, so rebuilding needs a live OpenSearch holding all 38,483
  indexed chunks — an untracked, machine-local artifact. On any machine
  without it, including the CUDA box the one training run happens on, these
  files cannot be regenerated at all.
- **The output depends on more than its inputs.** The negatives that come
  back are a function of the index contents *and* the base embedding model
  at mining time. Re-mining after either changes produces different
  triplets, so "deterministic" was never the guarantee it sounded like.
- **The size argument used the wrong number.** 27 MB is the working-tree
  size. Git stores blobs zlib-compressed and this is highly repetitive
  JSONL: measured by packing both files into a scratch repository, they add
  **2.89 MiB**, against a 12.02 MiB repository.

The deciding reason is provenance. These triplets are the sole input to the
project's only training run, and the retrieval delta claimed for that run
rests on them. An untracked input to a reported number is the failure this
repository's rules exist to prevent.

The 200-row `train.sample.jsonl` and 50-row `val.sample.jsonl` were removed
in the same change: they existed only to make the schema inspectable while
the real files were absent, and keeping them now would be a second copy free
to drift from the first.

## Rebuilding the splits

Only possible on a machine with the corpus indexed (`docker compose -f
docker/docker-compose.yml up -d`, then `python scripts/build_index.py`):

```
python scripts/mine_hard_negatives.py
```

`--limit N` does a quick partial pass. The eval-contamination guard in
`duediligence/train/synthetic.py` drops any query whose source passage is
labelled in `data/eval_set.jsonl`, so the training data cannot leak into the
retrieval measurement.
