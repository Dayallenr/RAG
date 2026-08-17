"""
Draft a co-validity review sheet for the verified eval questions.

The eval set labels one chunk per question, but the corpus frequently
contains several chunks that answer a question equally well. Every unlabelled
one of those scores as a *miss*, which is why CLAUDE.md records the retrieval
numbers as a floor rather than an estimate. Verifying that a label is correct
does not fix this — the label was already scoring as a hit. Only *adding* the
co-valid ids converts those false misses into hits.

This script does the legwork for that pass: for each verified question it runs
the project's best retriever, drops anything already labelled, and writes what
is left into a review sheet with a checkbox per candidate. A human ticks the
ones that also answer the question; ``apply_covalidity_review.py`` folds the
ticks back into the eval set.

Deliberately no automatic judgement. An agent deciding which chunks are
co-valid and then scoring retrieval against its own decisions is the
self-graded eval this whole exercise exists to escape.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from duediligence.config import load_config
from duediligence.index.embed import ChunkEmbedder
from duediligence.index.hybrid_search import hybrid_search
from duediligence.index.opensearch_client import build_client

logger = logging.getLogger(__name__)

# Deep enough that a genuinely co-valid chunk is very likely in the pool,
# shallow enough that a human is not asked to read 50 passages per question.
_CANDIDATE_K = 50
_SHOW = 8
_TEXT_CHARS = 420


def _truncate(text: str, limit: int = _TEXT_CHARS) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[:limit].rstrip() + " …"


def _describe(hit: dict) -> str:
    parts = [
        hit.get("company") or "?",
        hit.get("filing_type") or "?",
        hit.get("filing_date") or "?",
        hit.get("chunk_type") or "?",
    ]
    line = " · ".join(str(p) for p in parts)
    if hit.get("section"):
        line += f" · {hit['section']}"
    return line


def fetch_chunks(client, index_name: str, chunk_ids: list[str]) -> dict[str, dict]:
    """Look up labelled chunks by id — documents are keyed by ``chunk_id``."""
    if not chunk_ids:
        return {}
    response = client.mget(index=index_name, body={"ids": sorted(set(chunk_ids))})
    return {
        doc["_id"]: doc.get("_source", {})
        for doc in response.get("docs", [])
        if doc.get("found")
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", default="data/eval_set.jsonl")
    parser.add_argument("--out-md", default="data/eval_covalidity_review.md")
    parser.add_argument("--out-jsonl", default="data/eval_covalidity_candidates.jsonl")
    parser.add_argument("--limit", type=int, default=None, help="only the first N questions")
    parser.add_argument("--show", type=int, default=_SHOW, help="candidates shown per question")
    parser.add_argument(
        "--no-rerank", action="store_true",
        help="skip the cross-encoder (faster, lower-quality candidate ordering)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("opensearch").setLevel(logging.WARNING)

    config = load_config()
    entries = [
        json.loads(line)
        for line in Path(args.eval_set).read_text().splitlines()
        if line.strip()
    ]
    verified = [e for e in entries if e.get("verified")]
    if args.limit:
        verified = verified[: args.limit]
    logger.info("%d verified questions of %d total", len(verified), len(entries))

    client = build_client(config.opensearch)
    index_name = config.opensearch.index_name
    embedder = ChunkEmbedder(config.models.embedding_model)

    reranker = None
    if not args.no_rerank:
        from duediligence.index.rerank import CrossEncoderReranker

        reranker = CrossEncoderReranker(config.models.reranker_model)

    labelled = fetch_chunks(
        client, index_name, [cid for e in verified for cid in e.get("relevant_chunk_ids", [])]
    )

    rows: list[dict] = []
    md: list[str] = [
        "# Co-validity review",
        "",
        "Each question below already has a **correct** label. The question here is",
        "different: does any *other* chunk answer it as well? Every co-valid chunk left",
        "unlabelled is scored as a retrieval miss, which is what currently depresses the",
        "reported recall.",
        "",
        "**How to use this:** tick `[x]` for every candidate that genuinely also answers",
        "the question. Leave it unticked if it is off-topic, or if it merely mentions the",
        "subject without answering. When done, run:",
        "",
        "```",
        "python scripts/apply_covalidity_review.py",
        "```",
        "",
        "Ticking nothing for a question is a valid outcome — it means the single existing",
        "label really is the only chunk that answers it.",
        "",
        "---",
        "",
    ]

    for entry in verified:
        question = entry["question"]
        current = entry.get("relevant_chunk_ids", [])

        vector = embedder.embed_query(question)
        hits = hybrid_search(
            client, index_name, question, vector,
            k=_CANDIDATE_K, candidate_k=_CANDIDATE_K,
        )
        if reranker is not None:
            hits = reranker.rerank(question, hits, top_k=args.show + len(current))

        candidates = [h for h in hits if h.get("chunk_id") not in set(current)][: args.show]

        md.append(f"### `{entry['eval_id']}` — {question}")
        md.append("")
        for cid in current:
            source = labelled.get(cid, {})
            md.append(f"**Already labelled** `{cid}` — {_describe(source)}  ")
            md.append(f"> {_truncate(source.get('text', '(not found in index)'))}")
            md.append("")
        md.append("Also answers the question?")
        md.append("")
        for rank, hit in enumerate(candidates, start=1):
            md.append(f"- [ ] `{hit['chunk_id']}` — rank {rank} · {_describe(hit)}  ")
            md.append(f"      > {_truncate(hit.get('text', ''))}")
        md.append("")
        md.append("---")
        md.append("")

        rows.append({
            "eval_id": entry["eval_id"],
            "question": question,
            "current_chunk_ids": current,
            "candidate_chunk_ids": [h["chunk_id"] for h in candidates],
        })

    Path(args.out_md).write_text("\n".join(md))
    with Path(args.out_jsonl).open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    total_candidates = sum(len(r["candidate_chunk_ids"]) for r in rows)
    print(f"\n{len(rows)} questions, {total_candidates} candidates to judge")
    print(f"wrote {args.out_md}")
    print(f"wrote {args.out_jsonl}")


if __name__ == "__main__":
    main()
