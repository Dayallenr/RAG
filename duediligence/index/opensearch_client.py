"""
OpenSearch client, index mapping, and the two baseline search primitives
(dense k-NN and BM25) that Phase 5's hybrid search will combine.

One index holds both representations of every chunk — the analyzed ``text``
field for BM25 and the ``embedding`` knn_vector field for dense retrieval —
so hybrid search is one query against one index rather than a fan-out to
two systems whose scores then have to be fused across a network hop.

**Two backends, one interface.** ``local`` is the Docker container in
``docker/docker-compose.yml``: plain HTTP, no auth, localhost only. ``aws``
is AWS OpenSearch Service, reached with SigV4-signed requests using
whatever boto3 credentials are in the environment. Everything above this
module is backend-agnostic, which is the point — the Phase 12 cloud demo
should be a config change, not a code change.

**Documents are keyed by ``chunk_id``**, the content-addressed id from
``duediligence/ingest/schema.py``. Indexing is therefore idempotent: the
same chunk re-indexed overwrites itself instead of accumulating duplicates,
and a re-run after a partial failure is safe to just repeat.
"""
from __future__ import annotations

import json
import logging
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from opensearchpy import OpenSearch, helpers

from duediligence.config import OpenSearchConfig
from duediligence.index.embed import EMBEDDING_DIMENSION

logger = logging.getLogger(__name__)

__all__ = [
    "bm25_search",
    "build_client",
    "build_index_mapping",
    "bulk_index",
    "bulk_load_settings",
    "create_index",
    "document_count",
    "existing_chunk_ids",
    "iter_jsonl_chunks",
    "knn_search",
    "to_index_document",
]

# Fields carried into the index. ``embedding`` is excluded from search
# results everywhere below — returning 384 floats per hit would dominate
# the response payload for no benefit to any caller.
_SOURCE_EXCLUDES = ["embedding"]


def build_index_mapping() -> dict[str, Any]:
    """Index settings + mappings for the chunk corpus.

    ``number_of_replicas: 0`` because a single-node cluster has nowhere to
    put a replica shard — the default of 1 would leave the index yellow
    forever waiting for a second node that is never coming.

    The k-NN field uses the **lucene** engine with cosine similarity:
    cosine matches the normalized vectors ``embed.py`` produces, and lucene
    (rather than faiss/nmslib) keeps the vectors in the same Lucene segments
    as the inverted index, so there's no separate native memory pool to size
    and filtered k-NN works without extra configuration.
    """
    return {
        "settings": {
            "index": {
                "knn": True,
                "number_of_shards": 1,
                "number_of_replicas": 0,
            }
        },
        "mappings": {
            "properties": {
                "chunk_id": {"type": "keyword"},
                "company": {"type": "keyword"},
                "filing_type": {"type": "keyword"},
                "filing_date": {"type": "date"},
                "accession_number": {"type": "keyword"},
                # Never searched, only displayed as a citation link back to
                # sec.gov — indexing it would just grow the index.
                "source_url": {"type": "keyword", "index": False},
                "chunk_type": {"type": "keyword"},
                "hierarchy_level": {"type": "integer"},
                "parent_chunk_id": {"type": "keyword"},
                "section": {"type": "keyword"},
                "token_count": {"type": "integer"},
                # The English analyzer (stemming + stopwords) is what makes
                # the BM25 half of hybrid search competitive on prose like
                # "the Company's allowance for credit losses increased".
                "text": {"type": "text", "analyzer": "english"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": EMBEDDING_DIMENSION,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "lucene",
                        "parameters": {"ef_construction": 128, "m": 16},
                    },
                },
            }
        },
    }


def build_client(config: OpenSearchConfig, *, timeout: int = 60) -> OpenSearch:
    """Construct a client for whichever backend the config names."""
    if config.backend == "local":
        return OpenSearch(
            hosts=[config.local_endpoint],
            http_compress=True,
            use_ssl=config.local_endpoint.startswith("https"),
            verify_certs=False,
            ssl_show_warn=False,
            timeout=timeout,
            max_retries=3,
            retry_on_timeout=True,
        )

    if config.backend == "aws":
        # Imported lazily: boto3 credential resolution shouldn't run (or be
        # a hard dependency of importing this module) for local development,
        # which is every phase of this project except the gated Phase 12 demo.
        import boto3
        from opensearchpy import AWSV4SignerAuth, RequestsHttpConnection

        session = boto3.Session()
        credentials = session.get_credentials()
        if credentials is None:
            raise RuntimeError(
                "opensearch.backend is 'aws' but no AWS credentials were found; "
                "configure credentials or set backend back to 'local'."
            )
        return OpenSearch(
            hosts=[config.local_endpoint],
            http_auth=AWSV4SignerAuth(credentials, session.region_name, "es"),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=timeout,
            max_retries=3,
            retry_on_timeout=True,
        )

    raise ValueError(f"unknown opensearch backend {config.backend!r}; expected 'local' or 'aws'")


def create_index(client: OpenSearch, index_name: str, *, recreate: bool = False) -> bool:
    """Create the index if absent. Returns True if it was created.

    ``recreate=True`` deletes an existing index first — destructive, and
    only ever passed from a script flag the user typed, never by default.
    """
    exists = client.indices.exists(index=index_name)
    if exists and not recreate:
        return False
    if exists:
        logger.warning("deleting existing index %s", index_name)
        client.indices.delete(index=index_name)

    client.indices.create(index=index_name, body=build_index_mapping())
    logger.info("created index %s", index_name)
    return True


def to_index_document(chunk: dict[str, Any], embedding: list[float]) -> dict[str, Any]:
    """Shape one chunk dict (as written to data/**/*.jsonl) into a bulk action.

    Table chunks carry an extra ``rows`` field holding exact cell values;
    it's deliberately dropped here. Those exact values exist for the
    extraction eval to verify numbers against, not for retrieval, and the
    serialized ``text`` already contains the same content in the form the
    embedding and BM25 analyzer actually consume.
    """
    return {
        "_op_type": "index",
        "_id": chunk["chunk_id"],
        "_source": {
            "chunk_id": chunk["chunk_id"],
            "company": chunk["company"],
            "filing_type": chunk["filing_type"],
            "filing_date": chunk["filing_date"],
            "accession_number": chunk["accession_number"],
            "source_url": chunk["source_url"],
            "chunk_type": chunk["chunk_type"],
            "hierarchy_level": chunk["hierarchy_level"],
            "parent_chunk_id": chunk["parent_chunk_id"],
            "section": chunk["section"],
            "token_count": chunk.get("token_count"),
            "text": chunk["text"],
            "embedding": embedding,
        },
    }


def bulk_index(
    client: OpenSearch,
    index_name: str,
    actions: Iterable[dict[str, Any]],
    *,
    batch_size: int = 500,
) -> tuple[int, list[Any]]:
    """Bulk-index an iterable of actions, returning (succeeded, errors).

    ``raise_on_error=False`` so a handful of rejected documents surface as
    reportable errors at the end instead of aborting a multi-minute run that
    has already embedded everything.
    """
    succeeded, errors = helpers.bulk(
        client,
        actions,
        index=index_name,
        chunk_size=batch_size,
        request_timeout=120,
        raise_on_error=False,
        raise_on_exception=False,
    )
    return succeeded, list(errors)


@contextmanager
def bulk_load_settings(client: OpenSearch, index_name: str) -> Iterator[None]:
    """Suspend periodic refresh for the duration of a bulk load.

    With the default 1s refresh, a long indexing run keeps cutting small
    segments that then have to be merged — and for a k-NN index each new
    segment means building an HNSW graph, so that work is paid repeatedly on
    data that is still arriving. Setting ``refresh_interval: -1`` during the
    load and restoring it afterwards is the standard remedy.

    Restores in a ``finally`` so an interrupted run doesn't leave the index
    permanently un-refreshing, which would make it look empty to every
    subsequent search.
    """
    client.indices.put_settings(index=index_name, body={"index": {"refresh_interval": "-1"}})
    try:
        yield
    finally:
        client.indices.put_settings(index=index_name, body={"index": {"refresh_interval": "1s"}})
        client.indices.refresh(index=index_name)


def document_count(client: OpenSearch, index_name: str) -> int:
    client.indices.refresh(index=index_name)
    return int(client.count(index=index_name)["count"])


def existing_chunk_ids(client: OpenSearch, index_name: str) -> set[str]:
    """Every ``_id`` already in the index, for resuming an interrupted load.

    Indexing is idempotent (documents are keyed by content-addressed
    chunk_id), so a re-run is *correct* without this — it just re-embeds
    work already done, and embedding is the expensive half. Scanning ids
    with ``_source=False`` returns only the ids, which is small enough to
    hold in a set for a corpus this size.
    """
    if not client.indices.exists(index=index_name):
        return set()
    client.indices.refresh(index=index_name)
    return {
        hit["_id"]
        for hit in helpers.scan(
            client, index=index_name, query={"query": {"match_all": {}}}, _source=False, size=5000
        )
    }


def _filter_clauses(filters: dict[str, Any]) -> list[dict[str, Any]]:
    """Turn a field->value map into filter clauses.

    A list value becomes a ``terms`` clause (match any of), a scalar becomes
    ``term`` (match exactly). Passing a list to ``term`` is not an error in
    OpenSearch — it silently matches nothing — so the distinction has to be
    made here rather than left to the caller.
    """
    return [
        {"terms": {field: value}} if isinstance(value, (list, tuple, set))
        else {"term": {field: value}}
        for field, value in filters.items()
    ]


def _format_hits(response: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"chunk_id": hit["_id"], "score": hit["_score"], **hit.get("_source", {})}
        for hit in response["hits"]["hits"]
    ]


def knn_search(
    client: OpenSearch,
    index_name: str,
    query_vector: list[float],
    *,
    k: int = 10,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Dense retrieval: approximate nearest neighbors over the embeddings.

    ``filters`` is an optional field->value map (e.g. ``{"company": "COLB"}``)
    applied *inside* the k-NN clause, so the engine returns k results that
    already satisfy the filter rather than k global neighbors that a
    post-filter might reduce to almost nothing.
    """
    knn_clause: dict[str, Any] = {"vector": query_vector, "k": k}
    if filters:
        knn_clause["filter"] = {"bool": {"must": _filter_clauses(filters)}}

    response = client.search(
        index=index_name,
        body={
            "size": k,
            "query": {"knn": {"embedding": knn_clause}},
            "_source": {"excludes": _SOURCE_EXCLUDES},
        },
    )
    return _format_hits(response)


def bm25_search(
    client: OpenSearch,
    index_name: str,
    query: str,
    *,
    k: int = 10,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Lexical retrieval: OpenSearch's default BM25 over the analyzed text.

    The lexical baseline matters on this corpus specifically — filings are
    full of exact terminology ("allowance for credit losses", "Item 1A") and
    ticker symbols that a dense model can blur together but BM25 matches
    exactly.
    """
    must: list[dict[str, Any]] = [{"match": {"text": query}}]
    if filters:
        must += _filter_clauses(filters)

    response = client.search(
        index=index_name,
        body={
            "size": k,
            "query": {"bool": {"must": must}},
            "_source": {"excludes": _SOURCE_EXCLUDES},
        },
    )
    return _format_hits(response)


def iter_jsonl_chunks(paths: Iterable[str | Path]) -> Iterator[dict[str, Any]]:
    """Stream chunk dicts from jsonl files without holding the corpus in
    memory — 39k chunks of filing text is a few hundred MB decoded."""
    for path in paths:
        with Path(path).open() as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)
