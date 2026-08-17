"""Tests for synthetic training-query generation.

The contamination guard is the reason this module exists, so it gets the
most tests. "We remembered not to train on the test set" is not verifiable
after the fact; a failing test is.
"""
from __future__ import annotations

import json

import pytest

from duediligence.train.synthetic import (
    EvalLeakageError,
    assert_no_eval_leakage,
    build_prompt,
    eval_chunk_ids,
    eval_question_keys,
    is_contaminated,
    normalize_question,
    parse_questions,
)


class TestEvalChunkIds:
    def test_collects_every_labelled_chunk(self, tmp_path):
        path = tmp_path / "eval.jsonl"
        path.write_text(
            json.dumps({"eval_id": "r1", "relevant_chunk_ids": ["a", "b"]}) + "\n"
            + json.dumps({"eval_id": "r2", "relevant_chunk_ids": ["b", "c"]}) + "\n"
        )
        assert eval_chunk_ids(path) == {"a", "b", "c"}

    def test_questions_dropped_from_scoring_contribute_nothing(self, tmp_path):
        path = tmp_path / "eval.jsonl"
        path.write_text(json.dumps({"eval_id": "r1", "relevant_chunk_ids": []}) + "\n")
        assert eval_chunk_ids(path) == set()

    def test_a_missing_eval_set_is_a_hard_failure(self, tmp_path):
        # Silently generating with an empty exclusion set would contaminate
        # the test set while appearing to work.
        with pytest.raises(FileNotFoundError):
            eval_chunk_ids(tmp_path / "does-not-exist.jsonl")


class TestContamination:
    def test_an_identical_question_is_contaminated(self):
        question = "What is the date of the merger agreement between Columbia and Umpqua?"
        assert is_contaminated(question, [normalize_question(question)])

    def test_a_reworded_near_duplicate_is_contaminated(self):
        held_out = normalize_question(
            "What is the date of the merger agreement between Columbia and Umpqua?"
        )
        assert is_contaminated(
            "What is the date of the merger agreement between Umpqua and Columbia?", [held_out]
        )

    def test_an_unrelated_question_is_not_contaminated(self):
        held_out = normalize_question(
            "What is the date of the merger agreement between Columbia and Umpqua?"
        )
        assert not is_contaminated("How did PPP loans affect deposit balances in 2020?", [held_out])

    def test_an_empty_question_is_treated_as_contaminated(self):
        # Nothing useful can be trained on it, and letting it through would
        # put an empty string in the query field.
        assert is_contaminated("", [normalize_question("anything at all")])

    def test_empty_held_out_entries_are_skipped(self):
        assert not is_contaminated("A perfectly fine question about deposits?", [frozenset()])

    def test_the_threshold_is_configurable(self):
        held_out = normalize_question("net income for Columbia in 2023")
        question = "What was net income for Columbia in 2023?"
        assert is_contaminated(question, [held_out], threshold=0.5)
        assert not is_contaminated(question, [held_out], threshold=0.99)


class TestEvalQuestionKeys:
    def test_reads_every_question(self, tmp_path):
        path = tmp_path / "eval.jsonl"
        path.write_text(
            '{"question": "One thing?"}\n{"question": "Another thing?"}\n'
        )
        assert len(eval_question_keys(path)) == 2

    def test_blank_lines_are_skipped(self, tmp_path):
        path = tmp_path / "eval.jsonl"
        path.write_text('{"question": "One thing?"}\n\n')
        assert len(eval_question_keys(path)) == 1

    def test_a_missing_eval_set_is_a_hard_failure(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            eval_question_keys(tmp_path / "nope.jsonl")


class TestAssertNoEvalLeakage:
    def _eval_set(self, tmp_path, *questions):
        path = tmp_path / "eval.jsonl"
        path.write_text(
            "\n".join(json.dumps({"question": q, "relevant_chunk_ids": ["c1"]}) for q in questions)
        )
        return path

    def test_a_clean_training_set_passes(self, tmp_path):
        path = self._eval_set(tmp_path, "What was Columbia's net income in 2023?")
        # Returns the number of rows it cleared, so a caller can log it.
        assert assert_no_eval_leakage(["What are the merger termination fees?"], path) == 1

    def test_a_verbatim_eval_question_aborts(self, tmp_path):
        question = "What was Columbia's net income in 2023?"
        path = self._eval_set(tmp_path, question)
        with pytest.raises(EvalLeakageError):
            assert_no_eval_leakage([question], path)

    def test_a_question_differing_only_in_case_aborts(self, tmp_path):
        path = self._eval_set(tmp_path, "What was Columbia's net income in 2023?")
        with pytest.raises(EvalLeakageError):
            assert_no_eval_leakage(["WHAT WAS COLUMBIA'S NET INCOME IN 2023?"], path)

    def test_a_question_differing_only_in_punctuation_and_spacing_aborts(self, tmp_path):
        path = self._eval_set(tmp_path, "What was Columbia's net income in 2023?")
        with pytest.raises(EvalLeakageError):
            assert_no_eval_leakage(["What was  Columbia's net income in 2023"], path)

    def test_the_error_names_how_many_leaked(self, tmp_path):
        a, b = "What were the merger terms?", "Who approved the merger?"
        path = self._eval_set(tmp_path, a, b, "An unrelated question about deposits?")
        with pytest.raises(EvalLeakageError, match="2"):
            assert_no_eval_leakage([a, b, "Something else entirely?"], path)

    def test_a_missing_eval_set_is_a_hard_failure(self, tmp_path):
        # Refusing to train is correct: the guard cannot run without it.
        with pytest.raises(FileNotFoundError):
            assert_no_eval_leakage(["anything"], tmp_path / "does-not-exist.jsonl")

    def test_an_empty_training_set_passes_trivially(self, tmp_path):
        path = self._eval_set(tmp_path, "What was Columbia's net income in 2023?")
        assert assert_no_eval_leakage([], path) == 0


class TestBuildPrompt:
    def test_includes_provenance_and_text(self):
        prompt = build_prompt({
            "company": "COLB", "filing_type": "10-K", "filing_date": "2024-02-27",
            "text": "Net income was $348.7 million.",
        })
        assert "COLB" in prompt and "10-K" in prompt
        assert "Net income was $348.7 million." in prompt

    def test_asks_for_the_requested_number_of_questions(self):
        assert "write 5 distinct questions" in build_prompt({"text": "t"}, n=5).lower()

    def test_forbids_anaphoric_company_references(self):
        # Five banks share the corpus; "this bank" is unanswerable once the
        # question is separated from its passage.
        assert "do not write" in build_prompt({"text": "t"}).lower()


class TestParseQuestions:
    def test_extracts_plain_lines(self):
        raw = "What was net income in 2023?\nWhat drove the deposit decline?"
        assert len(parse_questions(raw)) == 2

    def test_strips_numbering_the_model_added_anyway(self):
        raw = "1. What was net income in 2023?\n2) What drove the deposit decline?"
        assert parse_questions(raw)[0] == "What was net income in 2023?"

    def test_strips_bullets(self):
        assert parse_questions("- What was net income in 2023?")[0] == (
            "What was net income in 2023?"
        )

    def test_drops_non_questions(self):
        # A declarative sentence in a query field trains the wrong thing.
        raw = "Here are three questions:\nNet income was $348 million.\nWhat was net income in 2023?"
        assert parse_questions(raw) == ["What was net income in 2023?"]

    def test_drops_preamble_even_when_it_ends_in_a_question_mark(self):
        raw = "Here are the questions you asked for?\nWhat was net income in 2023?"
        assert parse_questions(raw) == ["What was net income in 2023?"]

    def test_deduplicates(self):
        raw = "What was net income in 2023?\nWhat was net income in 2023?"
        assert len(parse_questions(raw)) == 1

    def test_caps_the_number_returned(self):
        raw = "\n".join(f"What was metric {i} in 2023 for Columbia?" for i in range(10))
        assert len(parse_questions(raw, max_questions=3)) == 3

    def test_strips_surrounding_quotes(self):
        assert parse_questions('"What was net income in 2023?"')[0] == (
            "What was net income in 2023?"
        )

    def test_an_empty_reply_yields_nothing(self):
        assert parse_questions("") == []
