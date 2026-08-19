"""The ANN sweep's arithmetic, its grid, and the operating point it picks.

#14 asks for a recall-versus-latency curve and for the chosen operating point
to be justified *against that curve*. The choice is therefore a function of the
measurements rather than a value written into a document by hand — these tests
drive that function, and the sentence generated from it, without a live cluster.

The measurement itself needs 38,483 real vectors, one rebuilt index per
build-parameter pair and a brute-force scan per query, so it is not unit-tested
here. It is run, and `results/ann_sweep/report.json` is the artifact.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sweep_ann.py"


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("sweep_ann", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _point(script, *, ef_search, recall, p95, label="m16-efc128", k=50):
    """One curve point, with only the fields the choice depends on."""
    return {
        "build": label,
        "k": k,
        "ef_search": ef_search,
        "ann_recall": recall,
        "latency_ms": {"mean": p95 / 2, "p50": p95 / 2, "p95": p95},
        "retrieval": {"recall@10": 0.6},
    }


class TestAnnRecall:
    def test_a_perfect_approximation_scores_one(self, script):
        exact = ["a", "b", "c"]
        assert script.ann_recall(["a", "b", "c"], exact, k=3) == 1.0

    def test_order_within_the_top_k_does_not_matter(self, script):
        # ANN recall asks which documents the graph reached, not how it
        # ranked them; ordering is what nDCG and MRR are for, and both are
        # reported separately from the labelled eval set.
        assert script.ann_recall(["c", "a", "b"], ["a", "b", "c"], k=3) == 1.0

    def test_a_missed_neighbour_costs_exactly_its_share(self, script):
        assert script.ann_recall(["a", "b", "z"], ["a", "b", "c"], k=3) == pytest.approx(2 / 3)

    def test_scores_against_the_top_k_of_the_ground_truth_only(self, script):
        # The ground truth is fetched once at the deepest k measured and
        # reused at every shallower k. Scoring a top-10 list against a
        # 50-long reference would cap it at 0.2 and call a perfect search a
        # failure.
        exact = [str(n) for n in range(50)]
        approximate = [str(n) for n in range(10)]
        assert script.ann_recall(approximate, exact, k=10) == 1.0

    def test_a_short_ground_truth_is_not_divided_by_the_requested_k(self, script):
        # A corpus with fewer than k documents cannot produce k neighbours,
        # and dividing by k there would report a recall no search could reach.
        assert script.ann_recall(["a", "b"], ["a", "b"], k=10) == 1.0


class TestSearchPoints:
    def test_the_default_point_is_measured_as_an_absent_parameter(self, script):
        # None is the configuration every published number in this project
        # was measured at, so the curve has to contain it.
        assert script.search_points([100, 200], k=10)[0] is None

    def test_points_below_k_are_dropped_rather_than_clamped(self, script):
        # ef_search < k returns a short result list rather than an error;
        # silently raising it to k instead would put a point on the curve
        # labelled with a value that was never searched.
        assert script.search_points([10, 50, 200], k=50) == [None, 50, 200]

    def test_points_are_swept_in_increasing_order(self, script):
        assert script.search_points([400, 100, 200], k=10) == [None, 100, 200, 400]


class TestChooseOperatingPoint:
    def test_picks_the_cheapest_point_that_reaches_the_target(self, script):
        points = [
            _point(script, ef_search=None, recall=0.71, p95=4.0),
            _point(script, ef_search=100, recall=0.97, p95=6.0),
            _point(script, ef_search=200, recall=0.995, p95=9.0),
            _point(script, ef_search=800, recall=1.0, p95=28.0),
        ]
        chosen, reached = script.choose_operating_point(points, target=0.99)
        assert reached is True
        assert chosen["ef_search"] == 200

    def test_falls_back_to_the_best_recall_when_no_point_reaches_the_target(self, script):
        points = [
            _point(script, ef_search=None, recall=0.71, p95=4.0),
            _point(script, ef_search=100, recall=0.88, p95=6.0),
        ]
        chosen, reached = script.choose_operating_point(points, target=0.99)
        # Reported as not reached rather than silently returning the last
        # point: "the target was met" and "nothing met it" have to be
        # distinguishable in the report.
        assert reached is False
        assert chosen["ef_search"] == 100

    def test_a_cheaper_point_wins_a_tie_on_recall(self, script):
        points = [
            _point(script, ef_search=200, recall=1.0, p95=9.0),
            _point(script, ef_search=800, recall=1.0, p95=28.0),
        ]
        chosen, _ = script.choose_operating_point(points, target=0.99)
        assert chosen["ef_search"] == 200

    def test_an_empty_curve_is_an_error_rather_than_a_default(self, script):
        with pytest.raises(ValueError, match="no curve points"):
            script.choose_operating_point([], target=0.99)


class TestJustification:
    def test_states_the_recall_and_the_latency_it_costs(self, script):
        baseline = _point(script, ef_search=None, recall=0.712, p95=4.0)
        chosen = _point(script, ef_search=200, recall=0.996, p95=9.0)
        sentence = script.justification(chosen, baseline, reached=True, target=0.99)
        assert "ef_search=200" in sentence
        assert "0.996" in sentence
        assert "0.712" in sentence

    def test_says_so_when_the_target_was_never_reached(self, script):
        baseline = _point(script, ef_search=None, recall=0.712, p95=4.0)
        chosen = _point(script, ef_search=800, recall=0.94, p95=28.0)
        sentence = script.justification(chosen, baseline, reached=False, target=0.99)
        # A sentence that reads the same whether or not the target was met
        # would let a re-run that degraded the index keep the old conclusion.
        assert "0.99" in sentence
        assert "not reach" in sentence

    def test_a_chosen_default_is_stated_as_no_change(self, script):
        baseline = _point(script, ef_search=None, recall=0.998, p95=4.0)
        sentence = script.justification(baseline, baseline, reached=True, target=0.99)
        assert "already" in sentence


class TestCompareExactLists:
    """Whether a rebuilt copy holds the source's vectors, or merely reordered
    documents the corpus scores identically. The build sweep's whole validity
    rests on this distinction, and the first real run hit it: 9 of 101 queries
    came back in a different order from copies whose vectors were fine."""

    def test_the_same_ranking_is_identical(self, script):
        assert script.compare_exact_lists(["a", "b"], [0.9, 0.8], ["a", "b"], [0.9, 0.8]) == "identical"

    def test_equal_scores_in_a_different_order_are_a_tie(self, script):
        # Order among equal scores follows Lucene's internal doc ids, which a
        # seven-segment index and a force-merged copy do not share.
        assert script.compare_exact_lists(["a", "b"], [0.8, 0.8], ["b", "a"], [0.8, 0.8]) == "tied"

    def test_a_reordering_of_unequal_scores_is_a_real_difference(self, script):
        # Exact search cannot rank a lower score above a higher one, so this
        # is the copy holding different vectors.
        assert script.compare_exact_lists(["a", "b"], [0.9, 0.8], ["b", "a"], [0.8, 0.9]) == "different"

    def test_a_tie_straddling_the_cut_is_a_tie(self, script):
        # Which of two documents scoring exactly at the k-th place makes the
        # top k is arbitrary in both indexes.
        assert (
            script.compare_exact_lists(["a", "b"], [0.9, 0.8], ["a", "c"], [0.9, 0.8]) == "tied"
        )

    def test_a_swapped_document_scoring_above_the_cut_is_a_real_difference(self, script):
        assert (
            script.compare_exact_lists(["a", "b"], [0.9, 0.7], ["a", "c"], [0.9, 0.85]) == "different"
        )


class TestBuildGrid:
    def test_labels_a_configuration_by_both_swept_parameters(self, script):
        config = script.BuildConfig(m=32, ef_construction=256)
        assert config.label == "m32-efc256"

    def test_index_names_are_namespaced_so_a_sweep_cannot_hit_a_served_index(self, script):
        # The sweep deletes every index it builds. A name collision with the
        # served index would make that cleanup destroy the corpus.
        name = script.sweep_index_name("duediligence-chunks-finetuned", script.BuildConfig(16, 128))
        assert name.startswith("ann-sweep-")
        assert "duediligence-chunks-finetuned" != name

    def test_the_grid_is_the_cross_product_in_a_stable_order(self, script):
        grid = script.build_grid([8, 16], [64, 128])
        assert [c.label for c in grid] == ["m8-efc64", "m8-efc128", "m16-efc64", "m16-efc128"]
