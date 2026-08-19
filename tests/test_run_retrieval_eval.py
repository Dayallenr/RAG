"""The retrieval eval's honesty guard.

The eval questions were drafted mechanically by reading sampled chunks, so a
run over an unverified set is self-graded. That is publishable; publishing it
without saying so is not. This is the check that the disclosure cannot be
quietly deleted.
"""
from __future__ import annotations

import pytest

from duediligence.eval.run_retrieval_eval import (
    guard_profiled_output,
    per_query_row,
    verification_note,
)


class TestVerificationNote:
    def test_warns_when_nothing_has_been_verified(self):
        note = verification_note(verified=0, total=101)
        assert note is not None
        assert "provisional" in note.lower()

    def test_the_warning_says_the_questions_were_drafted_automatically(self):
        note = verification_note(verified=0, total=101)
        assert "drafted" in note.lower()

    def test_warns_while_verification_is_partial(self):
        note = verification_note(verified=70, total=101)
        assert note is not None
        assert "70" in note and "101" in note

    def test_silent_once_every_question_is_verified(self):
        assert verification_note(verified=101, total=101) is None

    def test_the_warning_does_not_name_the_authoring_tool(self):
        note = verification_note(verified=0, total=101)
        assert "claude" not in note.lower()


class TestPerQueryRow:
    """A full-set run has to stay re-sliceable after the fact.

    The fine-tune delta reports a held-out figure and a full-set figure. If
    those came from two separate runs, any difference between the runs — a
    warm cache, a rebuilt index, a different day — would be indistinguishable
    from the fine-tune's effect. Carrying the split on the row lets both
    figures come from one set of retrievals.
    """

    entry = {
        "eval_id": "q1",
        "question": "What is the merger agreement date?",
        "question_type": "narrative",
        "company": "COLB",
        "chunk_type": "paragraph",
        "relevant_chunk_ids": ["gold"],
        "verified": True,
        "split": "test",
    }

    def test_carries_the_entrys_split(self):
        row = per_query_row(self.entry, {"bm25": ["gold"]})
        assert row["split"] == "test"

    def test_an_entry_with_no_split_records_none_rather_than_inventing_one(self):
        entry = {k: v for k, v in self.entry.items() if k != "split"}
        assert per_query_row(entry, {"bm25": ["gold"]})["split"] is None

    def test_records_each_retrievers_results_and_the_rank_of_the_label(self):
        row = per_query_row(self.entry, {"bm25": ["miss", "gold"], "dense": ["miss"]})
        assert row["bm25_retrieved"] == ["miss", "gold"]
        assert row["bm25_rank"] == 2
        assert row["dense_rank"] is None

    def test_carries_the_verification_flag_so_a_slice_can_count_it(self):
        row = per_query_row(self.entry, {"bm25": ["gold"]})
        assert row["verified"] is True


class TestProfiledRunsCannotClaimTheBaselinesArtifacts:
    """The default output path and run name belong to the published table.

    ``results/retrieval/report.json`` and the tracker run ``retrieval-eval``
    are the off-the-shelf model's numbers, and the tracker verifier diffs one
    against the other. A profiled run left on those defaults would overwrite
    the baseline report with a different model's figures and log them under
    the baseline's name — both artifacts would still look internally
    consistent, which is what makes it worth refusing rather than warning.
    """

    def test_a_profiled_run_on_the_default_output_is_refused(self):
        with pytest.raises(ValueError, match="--out"):
            guard_profiled_output(
                profile="finetuned",
                out="results/retrieval/report.json",
                run_name="retrieval-eval",
            )

    def test_the_message_names_the_profile_that_triggered_it(self):
        with pytest.raises(ValueError, match="finetuned"):
            guard_profiled_output(
                profile="finetuned",
                out="results/retrieval/report.json",
                run_name="retrieval-eval",
            )

    def test_a_profiled_run_writing_elsewhere_is_fine(self):
        guard_profiled_output(
            profile="finetuned",
            out="results/finetune_delta/finetuned-rerank.json",
            run_name="finetune-delta-finetuned-rerank",
        )

    def test_a_profiled_run_keeping_the_baseline_run_name_is_refused(self):
        # Writing elsewhere is not enough: the tracker check pairs a run name
        # with a report path, so the name alone can point the verifier at a
        # report this run did not write.
        with pytest.raises(ValueError, match="--run-name"):
            guard_profiled_output(
                profile="finetuned",
                out="results/finetune_delta/finetuned-rerank.json",
                run_name="retrieval-eval",
            )

    def test_the_unprofiled_baseline_run_is_untouched(self):
        guard_profiled_output(
            profile=None, out="results/retrieval/report.json", run_name="retrieval-eval"
        )
