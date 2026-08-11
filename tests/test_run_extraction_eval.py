from __future__ import annotations

from duediligence.eval.run_extraction_eval import _check_xbrl_entry

FAKE_FACTS = {
    "COLB": [
        {"concept": "NetIncomeLoss", "accession_number": "acc-1", "fiscal_period": "CY2022", "value": 100.0},
        {"concept": "NetIncomeLoss", "accession_number": "acc-1", "fiscal_period": "CY2023", "value": 348715000.0},
        {"concept": "Deposits", "accession_number": "acc-1", "fiscal_period": "CY2023", "value": 41607020000.0},
    ]
}


def test_exact_match_passes():
    entry = {"company": "COLB", "concept": "NetIncomeLoss", "accession_number": "acc-1", "expected_value": 348715000.0}
    result = _check_xbrl_entry(entry, {**FAKE_FACTS})
    assert result["passed"] is True
    assert result["actual_value"] == 348715000.0


def test_mismatched_value_fails():
    entry = {"company": "COLB", "concept": "NetIncomeLoss", "accession_number": "acc-1", "expected_value": 999.0}
    result = _check_xbrl_entry(entry, {**FAKE_FACTS})
    assert result["passed"] is False
    # Closest match (100.0) is still reported, not just a bare failure —
    # useful for diagnosing why an eval entry failed.
    assert result["actual_value"] == 100.0


def test_missing_fact_reports_not_found_not_a_crash():
    entry = {"company": "COLB", "concept": "DoesNotExist", "accession_number": "acc-1", "expected_value": 1.0}
    result = _check_xbrl_entry(entry, {**FAKE_FACTS})
    assert result["status"] == "fact_not_found"
    assert result["passed"] is False


def test_ambiguous_multiple_matches_picks_closest_to_expected():
    # Same concept+accession reported at multiple periods (e.g. quarterly
    # breakdowns inside an annual filing) — must pick the one nearest the
    # expected value, not just the first one found.
    entry = {"company": "COLB", "concept": "NetIncomeLoss", "accession_number": "acc-1", "expected_value": 100.5}
    result = _check_xbrl_entry(entry, {**FAKE_FACTS})
    assert result["actual_value"] == 100.0
    assert result["passed"] is False  # 100.5 vs 100.0 is outside the tight tolerance
