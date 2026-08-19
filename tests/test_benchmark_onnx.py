"""The ONNX benchmark's arithmetic, and the sentence it writes from it.

#13's acceptance criteria ask for the quality/speed trade-off to be stated
explicitly rather than only the speedup. The statement is generated from the
measurements rather than written by hand, so these tests drive the generator:
a sentence that could survive a re-run which changed the result is exactly the
stale claim this project's prime directive exists to prevent.

The measurement itself needs three real backends, a live index and 130MB of
weights, so it is not unit-tested — it is run, and `results/onnx/report.json`
is the artifact.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "benchmark_onnx.py"


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("benchmark_onnx", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestPercentile:
    def test_p50_of_an_odd_sample_is_a_value_that_was_measured(self, script):
        assert script.percentile([3.0, 1.0, 2.0], 0.5) == 2.0

    def test_p95_never_interpolates_between_measurements(self, script):
        values = [float(n) for n in range(1, 101)]
        assert script.percentile(values, 0.95) == 95.0

    def test_a_tiny_sample_still_returns_its_largest(self, script):
        assert script.percentile([7.0], 0.95) == 7.0

    def test_no_measurements_raises_rather_than_returning_zero(self, script):
        with pytest.raises(ValueError):
            script.percentile([], 0.5)


class TestDegradation:
    def test_a_loss_is_negative_and_in_the_metric_s_own_units(self, script):
        deltas = script.degradation({"recall@10": 0.6}, {"recall@10": 0.567})
        assert deltas["recall@10"] == pytest.approx(-0.033)

    def test_metrics_the_baseline_lacks_are_skipped_rather_than_assumed_zero(self, script):
        assert script.degradation({"recall@10": 0.6}, {"recall@10": 0.6, "mrr": 0.4}) == {
            "recall@10": 0.0
        }

    def test_recall_at_20_is_covered(self, script):
        # It was the only metric INT8 moved on the first real run; a table
        # without it reported "zero change on every metric".
        assert "recall@20" in script.degradation(
            {"recall@20": 0.683}, {"recall@20": 0.678}
        )


class TestSpeedup:
    def test_a_faster_variant_scores_above_one(self, script):
        assert script.speedup(14.1, 3.0) == pytest.approx(4.7, abs=0.01)

    def test_a_slower_variant_scores_below_one(self, script):
        assert script.speedup(3.0, 6.0) == 0.5


def summary(script, **overrides):
    base = {
        "query_latency_speedup_vs_torch": 4.73,
        "size_ratio_vs_torch": 0.26,
        "retrieval_delta_vs_torch": {"recall@10": -0.033},
        "identical_result_lists_vs_torch": 0,
    }
    return base | overrides


class TestParseArm:
    """An arm is a backend plus the hardware it ran on. Both belong in the
    label, because "ONNX is faster" and "CPU is faster at batch 1" are
    otherwise the same number."""

    def test_a_bare_backend_takes_the_default_device(self, script):
        arm = script.parse_arm("onnx-int8")
        assert (arm.label, arm.backend, arm.device) == ("onnx-int8", "onnx-int8", None)

    def test_a_pinned_torch_device_is_kept_in_the_label(self, script):
        arm = script.parse_arm("torch:cpu")
        assert (arm.label, arm.backend, arm.device) == ("torch:cpu", "torch", "cpu")

    def test_pinning_a_device_on_an_onnx_backend_raises(self, script):
        # The ONNX sessions are built with the CPU execution provider, so this
        # would label a measurement with hardware it never touched.
        with pytest.raises(ValueError, match="cannot pin a device"):
            script.parse_arm("onnx:cuda")


class TestTradeOffSentence:
    def test_it_names_the_cost_and_not_only_the_speedup(self, script):
        sentence = script.trade_off_sentence("onnx-int8", summary(script), queries=101, k=20)
        assert "4.73x" in sentence
        assert "-0.033 dense recall@10" in sentence

    def test_a_free_speedup_says_so_rather_than_printing_minus_zero(self, script):
        sentence = script.trade_off_sentence(
            "onnx",
            summary(
                script,
                retrieval_delta_vs_torch={"recall@10": 0.0},
                identical_result_lists_vs_torch=101,
            ),
            queries=101,
            k=20,
        )
        assert "no change in dense recall@10" in sentence

    def test_a_slower_variant_is_not_described_as_faster(self, script):
        sentence = script.trade_off_sentence(
            "onnx", summary(script, query_latency_speedup_vs_torch=0.5), queries=101, k=20
        )
        assert "faster" not in sentence
        assert "2.00x slower" in sentence

    def test_an_unchanged_metric_over_changed_results_says_both(self, script):
        """The measured case: INT8 scored identically on recall@1/5/10 while
        reordering every result list. Reporting only the metric would read as
        "the quantisation changed nothing", which is not what was measured."""
        sentence = script.trade_off_sentence(
            "onnx-int8",
            summary(
                script,
                retrieval_delta_vs_torch={"recall@10": 0.0},
                identical_result_lists_vs_torch=0,
            ),
            queries=101,
            k=20,
        )
        assert "no change in dense recall@10" in sentence
        assert "top-20 lists differ on 101 of 101 questions" in sentence

    def test_a_changed_metric_is_not_also_called_unchanged(self, script):
        """On the 30-question split the same backend did move recall@10. The
        reordering clause must not then claim the metrics held."""
        sentence = script.trade_off_sentence("onnx-int8", summary(script), queries=30, k=20)
        assert "-0.033 dense recall@10" in sentence
        assert "differ on 30 of 30 questions" in sentence
        assert "metrics are unchanged" not in sentence

    def test_identical_lists_are_stated_rather_than_left_implied(self, script):
        sentence = script.trade_off_sentence(
            "onnx",
            summary(
                script,
                retrieval_delta_vs_torch={"recall@10": 0.0},
                identical_result_lists_vs_torch=101,
            ),
            queries=101,
            k=20,
        )
        assert "identical on all 101 questions" in sentence

    def test_the_served_path_is_quoted_when_it_was_measured(self, script):
        """A degradation quoted only on the dense path describes a
        configuration nobody runs — this repo's own fine-tune finding in the
        opposite direction."""
        sentence = script.trade_off_sentence(
            "onnx-int8",
            summary(
                script,
                reranked_delta_vs_torch={"recall@10": 0.0},
                identical_reranked_lists_vs_torch=101,
            ),
            queries=101,
            k=20,
        )
        assert "served pipeline" in sentence
        assert "+0.000 recall@10 with 101 of 101 reranked lists identical" in sentence

    def test_a_model_with_no_file_here_is_not_reported_as_zero_bytes(self, script):
        # A Hub id resolves out of a shared cache; "0.00x the on-disk size"
        # would read as a measurement of something never weighed.
        sentence = script.trade_off_sentence(
            "onnx", summary(script, size_ratio_vs_torch=None), queries=101, k=20
        )
        assert "0.00x" not in sentence
        assert "not comparable" in sentence


def measurement(vectors, retrieved):
    array = np.asarray(vectors, dtype=np.float32)
    array = array / np.linalg.norm(array, axis=1, keepdims=True)
    return {"_query_vectors": array, "_passage_vectors": array, "_retrieved": retrieved}


class TestFidelityAndResultLists:
    def test_identical_vectors_score_a_cosine_of_one(self, script):
        one = measurement([[1.0, 0.0], [0.0, 1.0]], [["a"], ["b"]])
        result = script.fidelity(one, measurement([[1.0, 0.0], [0.0, 1.0]], [["a"], ["b"]]))
        assert result["query"]["min_cosine"] == pytest.approx(1.0)

    def test_the_worst_query_is_reported_not_only_the_average(self, script):
        baseline = measurement([[1.0, 0.0], [1.0, 0.0]], [["a"], ["b"]])
        variant = measurement([[1.0, 0.0], [0.0, 1.0]], [["a"], ["b"]])
        result = script.fidelity(baseline, variant)
        assert result["query"]["min_cosine"] == pytest.approx(0.0)
        assert result["query"]["mean_cosine"] == pytest.approx(0.5)

    def test_result_lists_count_order_not_only_membership(self, script):
        # A delta of 0.000 can mean "the same results" or "different results
        # that happen to score the same"; only one of those is a null effect.
        baseline = measurement([[1.0, 0.0]], [["a", "b"]])
        reordered = measurement([[1.0, 0.0]], [["b", "a"]])
        assert script.identical_result_lists(baseline, baseline) == 1
        assert script.identical_result_lists(baseline, reordered) == 0
