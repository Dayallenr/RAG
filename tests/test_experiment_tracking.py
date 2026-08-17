"""Tests for experiment tracking.

No test here touches the network or needs an account — the tracker module is
injected. The property most worth protecting is that tracking can never fail
a run: these scripts do expensive, rate-limited work, and losing it to a
telemetry outage would be an absurd trade.
"""
from __future__ import annotations

from duediligence.track import flatten_metrics, log_run, tracking_enabled


class FakeRun:
    def __init__(self, url: str = "https://wandb.ai/u/p/runs/abc123"):
        self.url = url
        self.logged: dict = {}
        self.finished = False

    def log(self, metrics):
        self.logged.update(metrics)

    def finish(self):
        self.finished = True


class FakeWandb:
    def __init__(self, run: FakeRun | None = None, *, raises: Exception | None = None):
        self.run = run or FakeRun()
        self.init_kwargs: dict = {}
        self._raises = raises

    def init(self, **kwargs):
        if self._raises:
            raise self._raises
        self.init_kwargs = kwargs
        return self.run


class TestFlattenMetrics:
    def test_nested_dicts_become_dotted_paths(self):
        flat = flatten_metrics({"retrievers": {"bm25": {"metrics": {"recall@10": 0.604}}}})
        assert flat == {"retrievers.bm25.metrics.recall@10": 0.604}

    def test_non_numeric_values_are_dropped(self):
        flat = flatten_metrics({"index": "duediligence-chunks", "queries": 101})
        assert flat == {"queries": 101}

    def test_booleans_are_not_treated_as_metrics(self):
        # Python bools are ints; without this, `verified: true` becomes the
        # metric `verified = 1` — schema masquerading as measurement.
        assert flatten_metrics({"verified": True, "queries": 5}) == {"queries": 5}

    def test_lists_of_dicts_are_indexed_not_dropped(self):
        # The ablation sweeps are lists, and their shape across parameter
        # values is the most interesting thing to plot.
        flat = flatten_metrics({"sweep": [{"recall": 0.1}, {"recall": 0.2}]})
        assert flat == {"sweep.0.recall": 0.1, "sweep.1.recall": 0.2}

    def test_per_query_is_skipped_by_default(self):
        flat = flatten_metrics({"per_query": [{"score": 1.0}] * 101, "queries": 101})
        assert flat == {"queries": 101}

    def test_long_lists_are_capped(self):
        flat = flatten_metrics({"rows": [{"v": 1.0}] * 500})
        assert len(flat) == 100

    def test_prose_caveats_are_not_metrics(self):
        assert flatten_metrics({"ground_truth_caveat": "labels are incomplete"}) == {}


class TestLogRun:
    def test_passes_config_and_metrics_through_and_returns_the_url(self):
        wandb = FakeWandb()
        url = log_run(
            name="retrieval-eval",
            config={"embedding_model": "bge-small-en-v1.5"},
            metrics={"recall@10": 0.703},
            wandb_module=wandb,
        )

        assert url == "https://wandb.ai/u/p/runs/abc123"
        assert wandb.init_kwargs["name"] == "retrieval-eval"
        assert wandb.init_kwargs["config"] == {"embedding_model": "bge-small-en-v1.5"}
        assert wandb.run.logged == {"recall@10": 0.703}

    def test_the_run_is_always_finished(self):
        wandb = FakeWandb()
        log_run(name="n", config={}, metrics={"m": 1.0}, wandb_module=wandb)
        assert wandb.run.finished is True

    def test_a_tracker_failure_returns_none_instead_of_raising(self):
        # Losing a full re-index or a day's model quota to a telemetry
        # outage would be an absurd trade.
        wandb = FakeWandb(raises=RuntimeError("network unreachable"))
        assert log_run(name="n", config={}, metrics={}, wandb_module=wandb) is None

    def test_a_failure_while_logging_still_finishes_the_run(self):
        class ExplodingRun(FakeRun):
            def log(self, metrics):
                raise RuntimeError("log failed")

        run = ExplodingRun()
        assert log_run(name="n", config={}, metrics={}, wandb_module=FakeWandb(run)) is None
        assert run.finished is True

    def test_tags_default_to_an_empty_list(self):
        wandb = FakeWandb()
        log_run(name="n", config={}, metrics={}, wandb_module=wandb)
        assert wandb.init_kwargs["tags"] == []


class TestTrackingEnabled:
    def test_disabled_without_an_api_key(self, monkeypatch):
        monkeypatch.delenv("WANDB_API_KEY", raising=False)
        monkeypatch.delenv("DUEDILIGENCE_TRACKING", raising=False)
        assert tracking_enabled() is False

    def test_enabled_with_an_api_key(self, monkeypatch):
        monkeypatch.setenv("WANDB_API_KEY", "secret")
        monkeypatch.delenv("DUEDILIGENCE_TRACKING", raising=False)
        assert tracking_enabled() is True

    def test_an_explicit_off_switch_beats_a_present_key(self, monkeypatch):
        # So a developer re-running an eval just to read its table does not
        # pollute the project's run history.
        monkeypatch.setenv("WANDB_API_KEY", "secret")
        monkeypatch.setenv("DUEDILIGENCE_TRACKING", "off")
        assert tracking_enabled() is False

    def test_logging_is_a_no_op_when_tracking_is_disabled(self, monkeypatch):
        monkeypatch.delenv("WANDB_API_KEY", raising=False)
        assert log_run(name="n", config={}, metrics={"recall@10": 0.7}) is None
