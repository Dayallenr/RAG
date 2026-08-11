from __future__ import annotations

import json

from duediligence.eval.run_chart_eval import run_chart_eval


def test_aggregates_hand_graded_verdicts(tmp_path):
    eval_set = tmp_path / "chart_eval_set.jsonl"
    eval_set.write_text(
        "\n".join(
            json.dumps(entry)
            for entry in [
                {"eval_id": "a", "chart_type_correct": True, "trend_direction_correct": True, "labels_correct": True},
                {"eval_id": "b", "chart_type_correct": True, "trend_direction_correct": False, "labels_correct": True},
            ]
        )
    )
    report = run_chart_eval(str(eval_set))
    assert report["total_graded"] == 2
    assert report["fully_correct"] == 1
    assert report["fully_correct_rate"] == 0.5
    assert report["per_criterion_correct"]["trend_direction_correct"] == 1
    assert report["per_criterion_correct"]["chart_type_correct"] == 2
