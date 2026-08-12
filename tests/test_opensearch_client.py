"""Tests for index mapping, document shaping, and query construction.

These run without a live cluster: the search functions are exercised
against a stub that records the request body, which is what actually needs
checking — a malformed k-NN or filter clause is accepted by OpenSearch and
silently returns the wrong results rather than erroring.
"""
from __future__ import annotations

import pytest

from duediligence.config import OpenSearchConfig
from duediligence.index.embed import EMBEDDING_DIMENSION
from duediligence.index.opensearch_client import (
    bm25_search,
    build_client,
    build_index_mapping,
    knn_search,
    to_index_document,
)


class StubClient:
    """Records the last search request and returns a canned response."""

    def __init__(self, hits=None):
        self.last_body = None
        self.last_index = None
        self._hits = hits if hits is not None else [
            {"_id": "abc123", "_score": 0.9, "_source": {"text": "hello", "company": "COLB"}}
        ]

    def search(self, *, index, body):
        self.last_index = index
        self.last_body = body
        return {"hits": {"hits": self._hits}}


def _chunk(**overrides):
    base = {
        "chunk_id": "abc123",
        "company": "COLB",
        "filing_type": "10-K",
        "filing_date": "2024-02-29",
        "accession_number": "0000887343-24-000024",
        "source_url": "https://www.sec.gov/Archives/edgar/data/887343/x.htm",
        "chunk_type": "paragraph",
        "hierarchy_level": 2,
        "parent_chunk_id": "parent1",
        "chunk_index": 3,
        "section": "Item 1A. Risk Factors",
        "token_count": 42,
        "text": "Nonaccrual loans totaled $33.1 million.",
    }
    base.update(overrides)
    return base


class TestIndexMapping:
    def test_knn_is_enabled_with_no_replicas(self):
        mapping = build_index_mapping()
        assert mapping["settings"]["index"]["knn"] is True
        # A single-node cluster cannot place a replica shard; the default of
        # 1 would leave the index yellow indefinitely.
        assert mapping["settings"]["index"]["number_of_replicas"] == 0

    def test_vector_dimension_matches_the_embedder(self):
        field = build_index_mapping()["mappings"]["properties"]["embedding"]
        assert field["type"] == "knn_vector"
        assert field["dimension"] == EMBEDDING_DIMENSION

    def test_cosine_space_matches_normalized_embeddings(self):
        method = build_index_mapping()["mappings"]["properties"]["embedding"]["method"]
        assert method["space_type"] == "cosinesimil"
        assert method["engine"] == "lucene"

    def test_text_uses_the_english_analyzer_for_bm25(self):
        text_field = build_index_mapping()["mappings"]["properties"]["text"]
        assert text_field["type"] == "text"
        assert text_field["analyzer"] == "english"


class TestToIndexDocument:
    def test_keys_document_by_content_addressed_chunk_id(self):
        action = to_index_document(_chunk(), [0.1] * EMBEDDING_DIMENSION)
        # Keying on chunk_id is what makes re-indexing idempotent.
        assert action["_id"] == "abc123"
        assert action["_op_type"] == "index"

    def test_drops_exact_table_rows(self):
        # Table chunks carry a "rows" field of exact cell values for the
        # extraction eval; it has no place in the retrieval index.
        action = to_index_document(
            _chunk(chunk_type="table", rows=[["a", "1"], ["b", "2"]]),
            [0.1] * EMBEDDING_DIMENSION,
        )
        assert "rows" not in action["_source"]

    def test_carries_embedding_and_metadata(self):
        action = to_index_document(_chunk(), [0.5] * EMBEDDING_DIMENSION)
        source = action["_source"]
        assert len(source["embedding"]) == EMBEDDING_DIMENSION
        assert source["section"] == "Item 1A. Risk Factors"
        assert source["accession_number"] == "0000887343-24-000024"

    def test_missing_token_count_does_not_raise(self):
        chunk = _chunk()
        del chunk["token_count"]
        assert to_index_document(chunk, [0.1] * EMBEDDING_DIMENSION)["_source"]["token_count"] is None


class TestKnnSearch:
    def test_builds_a_knn_query_excluding_the_embedding_from_results(self):
        client = StubClient()
        knn_search(client, "idx", [0.1] * EMBEDDING_DIMENSION, k=5)

        body = client.last_body
        assert body["size"] == 5
        assert body["query"]["knn"]["embedding"]["k"] == 5
        # Returning 384 floats per hit would dominate the response payload.
        assert body["_source"]["excludes"] == ["embedding"]

    def test_filters_are_applied_inside_the_knn_clause(self):
        client = StubClient()
        knn_search(client, "idx", [0.1] * EMBEDDING_DIMENSION, k=3, filters={"company": "COLB"})

        knn_clause = client.last_body["query"]["knn"]["embedding"]
        # Filtering inside the clause returns k results that already satisfy
        # the filter; a post-filter could reduce k hits to almost none.
        assert knn_clause["filter"]["bool"]["must"] == [{"term": {"company": "COLB"}}]

    def test_formats_hits_with_chunk_id_and_score(self):
        results = knn_search(StubClient(), "idx", [0.1] * EMBEDDING_DIMENSION, k=1)
        assert results[0]["chunk_id"] == "abc123"
        assert results[0]["score"] == 0.9
        assert results[0]["company"] == "COLB"


class TestBm25Search:
    def test_builds_a_match_query(self):
        client = StubClient()
        bm25_search(client, "idx", "allowance for credit losses", k=7)

        must = client.last_body["query"]["bool"]["must"]
        assert {"match": {"text": "allowance for credit losses"}} in must
        assert client.last_body["size"] == 7

    def test_filters_become_term_clauses(self):
        client = StubClient()
        bm25_search(client, "idx", "deposits", k=3, filters={"filing_type": "10-K"})
        assert {"term": {"filing_type": "10-K"}} in client.last_body["query"]["bool"]["must"]


class TestBuildClient:
    def test_unknown_backend_is_rejected(self):
        config = OpenSearchConfig(index_name="i", backend="elasticsearch", local_endpoint="http://x")
        with pytest.raises(ValueError, match="unknown opensearch backend"):
            build_client(config)

    def test_local_backend_builds_a_client(self):
        config = OpenSearchConfig(
            index_name="i", backend="local", local_endpoint="http://localhost:9200"
        )
        assert build_client(config) is not None


class TestFilterClauses:
    def test_scalar_filter_becomes_a_term_clause(self):
        client = StubClient()
        bm25_search(client, "idx", "q", k=3, filters={"company": "COLB"})
        assert {"term": {"company": "COLB"}} in client.last_body["query"]["bool"]["must"]

    def test_list_filter_becomes_a_terms_clause(self):
        # A list passed to `term` is not an error in OpenSearch — it silently
        # matches nothing, which would make an ablation look like a total
        # retrieval failure rather than a bug.
        client = StubClient()
        bm25_search(client, "idx", "q", k=3, filters={"chunk_type": ["paragraph", "table"]})
        assert {"terms": {"chunk_type": ["paragraph", "table"]}} in client.last_body["query"]["bool"]["must"]

    def test_list_filter_inside_knn_clause(self):
        client = StubClient()
        knn_search(client, "idx", [0.1] * EMBEDDING_DIMENSION, k=3,
                   filters={"chunk_type": ["paragraph", "table"]})
        must = client.last_body["query"]["knn"]["embedding"]["filter"]["bool"]["must"]
        assert {"terms": {"chunk_type": ["paragraph", "table"]}} in must
