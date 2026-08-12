"""Tests for structured-vs-semantic routing and exact XBRL lookup."""
from __future__ import annotations

import json

import pytest

from duediligence.route.query_router import Route, classify_query
from duediligence.route.structured_lookup import lookup_fact


class TestStructuredRouting:
    def test_full_lookup_key_routes_to_structured(self):
        decision = classify_query("What was Columbia's net income for 2023?")
        assert decision.route is Route.STRUCTURED
        assert decision.concept == "NetIncomeLoss"
        assert decision.company == "COLB"
        assert decision.fiscal_year == 2023

    def test_ticker_and_company_name_both_resolve(self):
        assert classify_query("COLB total assets 2022").company == "COLB"
        assert classify_query("Glacier Bancorp total assets 2022").company == "GBCI"

    def test_longest_concept_synonym_wins(self):
        # "net interest income" must not be shadowed by "interest income",
        # which maps to a different XBRL concept.
        assert classify_query("Columbia net interest income 2023").concept == "InterestIncomeExpenseNet"
        assert (
            classify_query("Columbia interest income 2023").concept
            == "InterestAndDividendIncomeOperating"
        )

    def test_decision_carries_a_readable_trace(self):
        reasons = classify_query("What was Columbia's net income for 2023?").reasons
        assert any("NetIncomeLoss" in r for r in reasons)
        assert any("complete lookup key" in r for r in reasons)


class TestSemanticFallback:
    @pytest.mark.parametrize(
        "query",
        [
            "What was net income?",  # no company, no year
            "What were total deposits in 2023?",  # no company
            "What was Columbia's net income?",  # no year
        ],
    )
    def test_incomplete_lookup_key_falls_back_to_semantic(self, query):
        # An exact lookup is a lookup on a composite key; guessing which of
        # five banks or fifteen years was meant would produce an
        # authoritative-looking answer for the wrong entity.
        assert classify_query(query).route is Route.SEMANTIC

    @pytest.mark.parametrize(
        "query",
        [
            "Why did Columbia's net income fall in 2023?",
            "Explain the movement in Wesbanco's net income in 2023.",
            "Compare Columbia's and Umpqua's total assets in 2021.",
            "What caused the change in SouthState's deposits in 2022?",
        ],
    )
    def test_narrative_markers_veto_a_complete_lookup_key(self, query):
        # These all name concept + company + year, so the key is complete —
        # but they ask for explanation, and a figure would not answer them.
        assert classify_query(query).route is Route.SEMANTIC

    def test_pure_narrative_question_routes_semantic(self):
        assert classify_query("What are the risks of the merger with Umpqua?").route is Route.SEMANTIC


class TestStructuredLookup:
    """Scored against data/extraction_eval_set.jsonl — the project's only
    ground truth with an unambiguous right answer, verified against the
    filings' own MD&A prose."""

    @pytest.fixture(scope="class")
    @classmethod
    def verified(cls):
        with open("data/extraction_eval_set.jsonl") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def test_returns_hand_verified_values(self, verified):
        for entry in verified:
            answer = lookup_fact(entry["concept"], entry["company"], 2023)
            assert answer is not None, f"no fact for {entry['company']} {entry['concept']}"
            assert answer.value == pytest.approx(entry["expected_value"], abs=1.0), entry["eval_id"]

    def test_selects_the_period_the_question_asked_for(self):
        # The regression this guards: Columbia's FY2023 10-K reports 2021,
        # 2022 and 2023 net income all labelled "FY2023FY". Selecting on the
        # label returned the 2022 comparative ($336.8M) for a 2023 question.
        answer = lookup_fact("NetIncomeLoss", "COLB", 2023)
        assert answer.period_start == "2023-01-01"
        assert answer.period_end == "2023-12-31"
        assert answer.value == pytest.approx(348_715_000.0)

    def test_instant_concept_returns_the_year_end_balance(self):
        answer = lookup_fact("Deposits", "COLB", 2023)
        assert answer.period_type == "instant"
        assert answer.period_end.startswith("2023-12")

    def test_prefers_the_original_filing_over_a_later_rounded_comparative(self):
        # A 2026 filing reports the same period rounded to $349,000,000.
        # The original as-filed figure is the traceable one.
        answer = lookup_fact("NetIncomeLoss", "COLB", 2023)
        assert answer.accession_number == "0000887343-24-000089"
        assert answer.value != 349_000_000.0

    def test_missing_year_returns_none_rather_than_a_nearest_guess(self):
        assert lookup_fact("NetIncomeLoss", "COLB", 1995) is None

    def test_unknown_company_returns_none(self):
        assert lookup_fact("NetIncomeLoss", "NOPE", 2023) is None


class TestFormatting:
    def test_billions_and_millions_render_readably(self):
        assert lookup_fact("Deposits", "COLB", 2023).formatted_value() == "$41.61 billion"
        assert lookup_fact("NetIncomeLoss", "COLB", 2023).formatted_value() == "$348.7 million"

    def test_answer_serializes_with_provenance(self):
        payload = lookup_fact("NetIncomeLoss", "COLB", 2023).to_dict()
        # Provenance is the point of the structured route — a number with no
        # traceable filing behind it is no better than a generated one.
        assert payload["accession_number"] == "0000887343-24-000089"
        assert payload["source_url"].startswith("https://www.sec.gov/")
        assert payload["period_end"] == "2023-12-31"
