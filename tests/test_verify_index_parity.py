"""Checking a profile's index against the baseline it will be compared against.

#22 builds a second index with a different embedding model and asserts two
things a reader cannot see: that it covers the same corpus as the baseline, and
that it actually holds the fine-tuned model's vectors. The second is the one
that fails silently — an index built with the wrong model returns plausible
rankings rather than an error, because cosine similarity across two incompatible
spaces is still a number. #23's delta would then be measuring nothing.

These tests drive the pure seams: what counts as a coverage mismatch, and what
counts as evidence that an index holds the model its profile names.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest
from opensearchpy.exceptions import NotFoundError

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_index_parity.py"


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("verify_index_parity", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BASELINE = {"paragraph": 28144, "table": 8671, "section": 1155, "document": 502}


class TestCountProblems:
    def test_identical_coverage_is_clean(self, script):
        assert script.count_problems(BASELINE, dict(BASELINE)) == []

    def test_a_short_chunk_type_is_reported_with_both_numbers(self, script):
        candidate = dict(BASELINE, table=8670)
        problems = script.count_problems(BASELINE, candidate)
        assert len(problems) == 1
        assert "table" in problems[0] and "8671" in problems[0] and "8670" in problems[0]

    def test_a_missing_chunk_type_is_reported_rather_than_skipped(self, script):
        candidate = {k: v for k, v in BASELINE.items() if k != "document"}
        problems = script.count_problems(BASELINE, candidate)
        assert any("document" in p for p in problems)

    def test_a_chunk_type_the_baseline_lacks_is_also_a_mismatch(self, script):
        candidate = dict(BASELINE, chart_description=11)
        assert any("chart_description" in p for p in script.count_problems(BASELINE, candidate))


def provenance(script, **kwargs):
    return script.Provenance(**{"index": "idx", "chunk_id": "abc", **kwargs})


class TestProvenanceProblems:
    def test_each_index_holding_its_own_vectors_is_clean(self, script):
        rows = [provenance(script, own=1.0, other=0.857)] * 3
        assert script.provenance_problems(rows) == []

    def test_an_index_built_with_the_wrong_model_is_caught(self, script):
        """The failure #22 exists to prevent: stored vectors are not this model's."""
        problems = script.provenance_problems([provenance(script, own=0.857, other=1.0)])
        assert problems and "abc" in problems[0]

    def test_two_indistinguishable_models_are_reported_not_passed(self, script):
        """The other model reproducing this index's vectors means the fine-tune
        did not move the weights, so a delta between them measures nothing."""
        assert script.provenance_problems([provenance(script, own=1.0, other=0.9999)])

    def test_the_failing_index_is_named_so_both_sides_are_distinguishable(self, script):
        rows = [provenance(script, index="chunks-finetuned", own=0.5, other=0.4)]
        assert "chunks-finetuned" in script.provenance_problems(rows)[0]

    def test_no_samples_is_a_failure_rather_than_a_pass(self, script):
        assert script.provenance_problems([])


class TestCoverageProblems:
    def test_identical_id_sets_are_clean(self, script):
        assert script.coverage_problems({"a", "b"}, {"a", "b"}) == []

    def test_equal_counts_of_different_chunks_are_caught(self, script):
        """The reason coverage is an id diff and not a document count: two
        indexes can hold the same number of different chunks."""
        problems = script.coverage_problems({"a", "b"}, {"a", "c"})
        assert len(problems) == 2
        assert "not the candidate" in problems[0] and "b" in problems[0]
        assert "not the baseline" in problems[1] and "c" in problems[1]

    def test_an_unfinished_candidate_build_is_named_as_such(self, script):
        problems = script.coverage_problems({"a", "b", "c"}, {"a"})
        assert "did not finish" in problems[0] and "2 chunks" in problems[0]

    def test_a_large_gap_is_summarised_rather_than_listed_in_full(self, script):
        problems = script.coverage_problems({f"c{i}" for i in range(200)}, set())
        assert "and 195 more" in problems[0]


class TestProfileUnset:
    def test_the_baseline_is_not_read_through_an_exported_profile(self, script, monkeypatch):
        """load_config() honours the env var, and this ticket's documented
        workflow exports it — so an unpinned baseline is the candidate."""
        monkeypatch.setenv("DUEDILIGENCE_CONFIG_PROFILE", "finetuned")
        with script.profile_unset():
            assert "DUEDILIGENCE_CONFIG_PROFILE" not in os.environ
        assert os.environ["DUEDILIGENCE_CONFIG_PROFILE"] == "finetuned"

    def test_an_unset_variable_is_left_unset(self, script, monkeypatch):
        monkeypatch.delenv("DUEDILIGENCE_CONFIG_PROFILE", raising=False)
        with script.profile_unset():
            pass
        assert "DUEDILIGENCE_CONFIG_PROFILE" not in os.environ


class TestStoredDocument:
    def test_a_missing_chunk_becomes_a_reported_problem_not_a_traceback(self, script):
        """A partial candidate index is what this script exists to find, so the
        lookup must not abort the run before the report is written."""
        class FakeClient:
            def get(self, index, id):
                raise NotFoundError(404, "not_found", {})

        assert script.stored_document(FakeClient(), "chunks", "abc") is None

    def test_a_present_chunk_returns_its_source(self, script):
        class FakeClient:
            def get(self, index, id):
                return {"_source": {"text": "hello", "embedding": [0.1]}}

        assert script.stored_document(FakeClient(), "chunks", "abc")["text"] == "hello"


class TestSampleIds:
    def test_ids_are_drawn_from_every_chunk_type(self, script):
        """Sampling paragraphs alone would leave tables — where dense retrieval
        is weakest, so where #23's delta matters most — unverified."""
        class FakeClient:
            def search(self, index, body):
                assert body["aggs"]["by_type"]["aggs"]["examples"]["top_hits"]["size"] == 2
                return {"aggregations": {"by_type": {"buckets": [
                    {"key": "paragraph", "examples": {"hits": {"hits": [{"_id": "p1"}, {"_id": "p2"}]}}},
                    {"key": "table", "examples": {"hits": {"hits": [{"_id": "t1"}]}}},
                ]}}}

        assert script.sample_ids(FakeClient(), "chunks", 2) == ["p1", "p2", "t1"]


class TestIndexCounts:
    def test_counts_come_from_the_aggregation_not_the_capped_hit_total(self, script):
        """`hits.total.value` caps at 10,000, so two 38k indexes both report
        10,000 and compare equal while differing."""
        class FakeClient:
            def search(self, index, body):
                return {
                    "hits": {"total": {"value": 10000, "relation": "gte"}},
                    "aggregations": {"chunk_type": {"buckets": [
                        {"key": "paragraph", "doc_count": 28144},
                        {"key": "table", "doc_count": 8671},
                    ]}},
                }

        assert script.index_counts(FakeClient(), "any") == {"paragraph": 28144, "table": 8671}
