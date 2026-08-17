# Handoff: PC session (Windows + RTX 5070)

A Claude Code session on the Windows PC does one job: **run the local model.**
The Mac keeps the OpenSearch index, the embeddings, and the Gemini key.

Read `CLAUDE.md` first — it loads automatically and carries the project's
rules and verified findings. This file covers only what is specific to this
machine and would otherwise have to be re-derived.

---

## Why this split exists

The two machines are on different networks (Mac `10.0.0.x`, PC `172.16.0.x`),
so the Mac cannot call the PC's Ollama server directly. **Git is the
transport.** The PC pulls inputs, generates, commits outputs, pushes. Nothing
is copied by hand and every artifact is versioned.

The PC exists in this project for one reason, and it is arithmetic. The
hosted model's free tier allows a verified 20 requests/day. Generating ~4,000
synthetic training queries would take **200 days** on that quota. On the
5070 it takes one sitting. Same reason for the 101 eval answers: six days
hosted, one sitting locally.

---

## Setup

```powershell
git clone https://github.com/Dayallenr/RAG.git
cd RAG
python -m pip install requests
```

That is the whole dependency list for this job. The script deliberately
pulls in **no torch, no sentence-transformers, no OpenSearch client** — that
was verified, not assumed. Do not install `requirements.txt` here; it drags
in a CUDA torch build this job never uses.

Everything the script reads is tracked in git: `data/chunks/` (27 MB),
`data/tables/` (47 MB), `data/eval_set.jsonl`. The 762 MB of raw filings is
gitignored and not needed.

Confirm Ollama:

```powershell
ollama list                 # must show qwen3:8b
curl http://localhost:11434 # must say "Ollama is running"
```

---

## Job 1 — synthetic training queries (issue #9)

Smoke-test first. Ten chunks, a minute or two, and it proves the model's
output actually parses before committing to the full run:

```powershell
python scripts/generate_synthetic_queries.py --limit 10
```

Then read `data/training/synthetic_queries.jsonl` and **actually look at the
questions**. They should be specific, name a company, and be answerable from
a filing. If they are vague ("What does the company do?") or the parser kept
preamble lines, stop and report it rather than generating 4,000 bad ones.

Full run:

```powershell
python scripts/generate_synthetic_queries.py
```

1,600 chunks × up to 3 questions ≈ 4,000–4,800 queries. Resumable — a
re-run skips finished chunks, so an interrupt costs nothing.

Then push:

```powershell
git add data/training/synthetic_queries.jsonl
git commit -m "Generate synthetic training queries with qwen3:8b (refs #9)"
git push origin main
```

---

## Hard rules

**Do not disable or weaken the contamination guard.** Every chunk the eval
set is labelled against (103 of them) is excluded, and generated queries too
similar to an eval question are dropped. This is the difference between a
fine-tuning result that measures generalisation and one that measures
memorisation of the test set. If it drops a lot of queries, report the
number — do not raise the threshold.

**Do not modify `data/eval_set.jsonl`.** 70 of 101 entries are
human-verified. It is the held-out test set.

**Do not re-open settled scope.** Decided already, do not re-litigate:
fine-tuning is limited to the retrieval models (bi-encoder first, then
cross-encoder); generation runs locally while Gemini judges independently;
the eval-set co-validity pass is **out of scope**, so reported recall stays
a floor rather than an estimate.

**Do not run the indexing or retrieval scripts here.** No OpenSearch on this
machine. `build_index.py`, `run_retrieval_eval.py` and `run_ablations.py`
belong on the Mac.

**Report honestly.** This project's prime directive is that every claim maps
to a real artifact. If the model produces poor questions, say so — a smaller
set of good training data beats 4,000 bad pairs, and a quietly bad dataset
would poison the fine-tuning result that depends on it.

---

## Report back

1. How many queries were written, and how many were dropped as contaminated.
2. The chunk-type breakdown printed at the end.
3. Your honest read on question quality from a sample of ~20.
4. Whether the `qwen3:8b` output needed reasoning-block stripping (the
   backend strips `<think>...</think>`; if raw reasoning is still leaking
   into queries, that is a bug worth reporting).

---

## Job 2 — answers for the eval set (issue #3)

**Ready now.** `data/generation/retrieval_contexts.jsonl` is committed: 101
questions, retrieval already done on the machine with the index. Pull first
(`git pull`), then:

```powershell
python scripts/generate_answers_locally.py --limit 5    # smoke test
python scripts/generate_answers_locally.py              # the rest
```

**Only 89 of the 101 call the model.** The other 12 route to exact XBRL
lookup and are passed through untouched — their answer is already a precise
figure with the accession number that reported it, and restating an exact
number through a language model can only introduce error.

Expect roughly 20–40 minutes. Resumable, same as Job 1.

Check a few answers before pushing. Each should cite passages as `[1]`,
`[2]`, and should say *"The provided filings do not state this."* rather than
guess when the passages do not contain the answer. A refusal is a **correct**
outcome here, not a failure — for a due-diligence tool an invented figure is
the catastrophic result.

```powershell
git add results/generation/answers.jsonl
git commit -m "Generate eval answers locally with qwen3:8b (refs #3)"
git push origin main
```

Judging happens back on the Mac, where the hosted key lives — deliberately a
**different model** from the one that generated, so the groundedness score
is not self-assessment.
