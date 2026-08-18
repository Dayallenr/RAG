"""The retrieval eval's honesty guard.

The eval questions were drafted mechanically by reading sampled chunks, so a
run over an unverified set is self-graded. That is publishable; publishing it
without saying so is not. This is the check that the disclosure cannot be
quietly deleted.
"""
from __future__ import annotations

from duediligence.eval.run_retrieval_eval import verification_note


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
