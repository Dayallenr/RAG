"""Tests for the hosted-run verification.

No test here touches the network. The fetch is injected, exactly as the
tracker module injects ``wandb`` — the point of the seam is that the
comparison logic, which is what decides whether a public claim is true, can
be exercised without an account, a key, or a live third party.

The property most worth protecting is that a *missing* metric fails. A
comparison that silently scores zero shared keys as "everything matched"
would certify an empty run as reproducing the report.
"""
from __future__ import annotations

import json

import pytest

from duediligence.track.verify import (
    LocalReport,
    ProjectNotPublicError,
    accepts_public_writes,
    compare_run,
    describe_access,
    fetch_public_project,
    latest_finished_runs,
    verify_runs,
)


def _run(name, display_name, created_at, summary, state="finished"):
    return {
        "name": name,
        "displayName": display_name,
        "createdAt": created_at,
        "state": state,
        "summaryMetrics": json.dumps(summary),
    }


class TestLatestFinishedRuns:
    def test_the_newest_run_of_each_name_wins(self):
        runs = [
            _run("old", "ablations", "2026-08-18T02:20:39Z", {"queries": 71}),
            _run("new", "ablations", "2026-08-18T02:53:23Z", {"queries": 71}),
        ]
        assert latest_finished_runs(runs)["ablations"]["name"] == "new"

    def test_a_crashed_run_is_never_the_citation(self):
        """A crashed run's summary is a partial write, not a result."""
        runs = [
            _run("good", "ablations", "2026-08-18T02:20:39Z", {"queries": 71}),
            _run("crashed", "ablations", "2026-08-18T02:53:23Z", {}, state="crashed"),
        ]
        assert latest_finished_runs(runs)["ablations"]["name"] == "good"

    def test_runs_with_unparseable_summaries_are_skipped(self):
        runs = [{"name": "x", "displayName": "ablations", "createdAt": "1", "state": "finished"}]
        assert latest_finished_runs(runs) == {}


class TestCompareRun:
    def test_identical_metrics_match(self):
        result = compare_run(
            {"retrievers.bm25.metrics.recall@10": 0.604},
            {"retrievers": {"bm25": {"metrics": {"recall@10": 0.604}}}},
        )
        assert result["ok"] is True
        assert result["compared"] == 1
        assert result["matched"] == 1

    def test_a_changed_value_is_a_mismatch(self):
        result = compare_run(
            {"retrievers.bm25.metrics.recall@10": 0.604},
            {"retrievers": {"bm25": {"metrics": {"recall@10": 0.703}}}},
        )
        assert result["ok"] is False
        assert result["mismatched"] == [
            {"metric": "retrievers.bm25.metrics.recall@10", "hosted": 0.604, "local": 0.703}
        ]

    def test_a_metric_the_host_never_received_fails(self):
        """The failure this whole check exists for: a report re-run after logging."""
        result = compare_run({}, {"queries": 101})
        assert result["ok"] is False
        assert result["missing_from_hosted"] == ["queries"]
        assert result["matched"] == 0

    def test_a_metric_only_on_the_server_fails(self):
        result = compare_run({"queries": 101, "dropped": 3}, {"queries": 101})
        assert result["ok"] is False
        assert result["only_in_hosted"] == ["dropped"]

    def test_wandb_internal_keys_are_not_metrics(self):
        result = compare_run(
            {"_step": 0, "_runtime": 0, "_timestamp": 1787021604.0, "queries": 101},
            {"queries": 101},
        )
        assert result["ok"] is True
        assert result["compared"] == 1

    def test_prose_in_the_report_is_not_compared(self):
        """``flatten_metrics`` drops caveats and per-query rows; so does this."""
        result = compare_run(
            {"queries": 101},
            {"queries": 101, "ground_truth_caveat": "labels are a floor", "per_query": [{"a": 1}]},
        )
        assert result["ok"] is True
        assert result["compared"] == 1

    def test_float_noise_within_tolerance_still_matches(self):
        result = compare_run({"recall@10": 0.703}, {"recall@10": 0.703 + 1e-12})
        assert result["ok"] is True

    def test_an_empty_report_cannot_pass(self):
        """Zero shared metrics is not evidence of anything."""
        assert compare_run({}, {})["ok"] is False


class TestVerifyRuns:
    def test_every_run_matching_verifies_the_project(self):
        runs = [_run("abc", "ablations", "2026-08-18T02:53:23Z", {"queries": 71})]
        result = verify_runs(runs, [LocalReport("ablations", "results/a.json", {"queries": 71})])

        assert result["verified"] is True
        assert result["metrics_compared"] == 1
        assert result["metrics_matched"] == 1
        assert result["runs"][0]["run_id"] == "abc"
        assert result["runs"][0]["report"] == "results/a.json"

    def test_one_bad_run_fails_the_whole_check(self):
        runs = [
            _run("abc", "ablations", "2026-08-18T02:53:23Z", {"queries": 71}),
            _run("def", "routing-eval", "2026-08-18T02:21:44Z", {"total": 36}),
        ]
        result = verify_runs(
            runs,
            [
                LocalReport("ablations", "results/a.json", {"queries": 71}),
                LocalReport("routing-eval", "results/r.json", {"total": 35}),
            ],
        )
        assert result["verified"] is False

    def test_a_report_with_no_hosted_run_fails_rather_than_being_skipped(self):
        result = verify_runs([], [LocalReport("ablations", "results/a.json", {"queries": 71})])

        assert result["verified"] is False
        assert result["runs"][0]["ok"] is False
        assert "no finished run" in result["runs"][0]["reason"]

    def test_run_urls_point_at_the_public_project(self):
        runs = [_run("abc", "ablations", "2026-08-18T02:53:23Z", {"queries": 71})]
        result = verify_runs(
            runs,
            [LocalReport("ablations", "results/a.json", {"queries": 71})],
            entity="ent",
            project="proj",
        )
        assert result["runs"][0]["run_url"] == "https://wandb.ai/ent/proj/runs/abc"


class TestFetchPublicProject:
    def test_an_anonymous_read_returns_the_runs(self):
        payload = {
            "data": {
                "project": {
                    "access": "USER_WRITE",
                    "runCount": 10,
                    "runs": {"edges": [{"node": {"name": "abc"}}]},
                }
            }
        }
        captured: dict = {}

        def fake_fetch(url, body, headers):
            captured.update(url=url, body=body, headers=headers)
            return payload

        project = fetch_public_project("ent", "proj", fetch=fake_fetch)

        assert project["runs"] == [{"name": "abc"}]
        assert project["access"] == "USER_WRITE"
        assert captured["url"].startswith("https://api.wandb.ai/")

    def test_no_credentials_are_ever_sent(self, monkeypatch):
        """The anonymous read *is* the public-visibility check.

        Sending a key would make a private project look public, which is the
        one way this script could certify something false.
        """
        monkeypatch.setenv("WANDB_API_KEY", "secret-key")
        captured: dict = {}

        def fake_fetch(url, body, headers):
            captured.update(headers=headers, body=body)
            return {"data": {"project": {"access": "PUBLIC", "runCount": 0, "runs": {"edges": []}}}}

        fetch_public_project("ent", "proj", fetch=fake_fetch)

        serialized = json.dumps(captured).lower()
        assert "secret-key" not in serialized
        assert not any(key.lower() == "authorization" for key in captured["headers"])

    def test_a_private_project_reads_as_null_and_raises(self):
        def fake_fetch(url, body, headers):
            return {"data": {"project": None}}

        with pytest.raises(ProjectNotPublicError):
            fetch_public_project("ent", "proj", fetch=fake_fetch)

    def test_a_graphql_error_raises(self):
        def fake_fetch(url, body, headers):
            return {"errors": [{"message": "permission denied"}]}

        with pytest.raises(ProjectNotPublicError) as error:
            fetch_public_project("ent", "proj", fetch=fake_fetch)
        assert "permission denied" in str(error.value)


class TestAccessLevel:
    """What the project's ``access`` field means for a reader.

    Established by comparison, not by reading documentation: four known-public
    projects (``wandb/gallery``, ``stacey/estuary``, ``borisd13/dalle-mini``,
    ``wandb/huggingface``) all report ``USER_READ``.
    """

    def test_public_is_read_only_to_strangers(self):
        assert accepts_public_writes("USER_READ") is False
        assert "anyone can view" in describe_access("USER_READ")

    def test_open_lets_anyone_submit_runs(self):
        assert accepts_public_writes("USER_WRITE") is True
        assert "submit runs" in describe_access("USER_WRITE")

    def test_an_unknown_access_level_is_reported_not_guessed(self):
        assert accepts_public_writes("SOMETHING_NEW") is False
        assert "SOMETHING_NEW" in describe_access("SOMETHING_NEW")

    def test_the_verdict_records_how_open_the_project_is(self):
        runs = [_run("abc", "ablations", "2026-08-18T02:53:23Z", {"queries": 71})]
        result = verify_runs(
            runs,
            [LocalReport("ablations", "results/a.json", {"queries": 71})],
            access="USER_WRITE",
        )
        assert result["accepts_public_writes"] is True
        assert result["verified"] is True, "an open project is a warning, not a failed check"
