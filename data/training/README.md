# Training data

Fine-tuning triplets for the bi-encoder, built from the corpus in three steps.

| File | Tracked | What it is |
|---|---|---|
| `synthetic_queries.jsonl` | yes | Generated queries, one per sampled passage. The input the splits are derived from. |
| `train.jsonl` | **no** (~24 MB) | Mined `(query, positive, hard negative)` triplets. |
| `val.jsonl` | **no** (~2.8 MB) | Same, held out by query so no query straddles the split. |
| `train.sample.jsonl` | yes | First 200 rows of `train.jsonl`. |
| `val.sample.jsonl` | yes | First 50 rows of `val.jsonl`. |

The two large splits are not tracked. They are deterministic output of a
script whose inputs *are* tracked, so committing 27 MB of them buys nothing
a reader cannot rebuild — and a clone dominated by regenerable blobs is
worse than one that is not. The samples stay tracked so the shape of the
data is inspectable without regenerating anything: same keys, same schema,
same source, just fewer rows.

## Rebuilding the splits

Needs a running OpenSearch with the corpus indexed (`docker compose -f
docker/docker-compose.yml up -d`, then `python scripts/build_index.py`),
because negatives are mined by running the *current* retriever and keeping
the top hits that are not the passage the query came from:

```
python scripts/mine_hard_negatives.py
```

`--limit N` does a quick partial pass. The eval-contamination guard in
`duediligence/train/synthetic.py` drops any query whose source passage is
labelled in `data/eval_set.jsonl`, so the training data cannot leak into the
retrieval measurement.
