"""The seams of the served-profile check.

#24's claim is that an environment variable changes what the running service
serves. The check that backs it has two judgements a reader has to trust: what
counts as the service misreporting itself, and what counts as two arms being
genuinely different rather than the same run under two labels. Both are pure
functions, and these tests drive them without standing up a model or an index.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

from duediligence.config import PROFILE_ENV_VAR

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_served_profile.py"


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("verify_served_profile", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


FINETUNED = {
    "profile": "finetuned",
    "model": "models/bge-small-duediligence",
    "index": "duediligence-chunks-finetuned",
}


class TestIdentityProblems:
    def _check(self, script, reported):
        return script.identity_problems(
            expected_profile="finetuned",
            expected_model="models/bge-small-duediligence",
            expected_index="duediligence-chunks-finetuned",
            reported=reported,
        )

    def test_a_matching_report_has_no_problems(self, script):
        assert self._check(script, FINETUNED) == []

    def test_a_stale_model_is_named_with_both_values(self, script):
        """The message has to carry what was served as well as what was
        wanted — "wrong model" sends someone back to the container to find out
        which one."""
        reported = {**FINETUNED, "model": "BAAI/bge-small-en-v1.5"}
        problems = self._check(script, reported)
        assert len(problems) == 1
        assert "BAAI/bge-small-en-v1.5" in problems[0]
        assert "models/bge-small-duediligence" in problems[0]

    def test_the_mismatched_pair_is_reported_as_one_problem_per_half(self, script):
        """A right model on a wrong index is the silent failure the endpoint
        exists to expose. Collapsing it to a single "mismatch" would hide
        which half moved, which is the first thing an operator needs."""
        reported = {**FINETUNED, "index": "duediligence-chunks"}
        problems = self._check(script, reported)
        assert len(problems) == 1
        assert "index" in problems[0]

    def test_a_missing_field_is_a_problem_not_a_crash(self, script):
        """An older image that does not report identity at all must fail the
        check rather than raise inside it."""
        assert len(self._check(script, {})) == 3

    def test_the_base_arm_expects_a_null_profile(self, script):
        problems = script.identity_problems(
            expected_profile=None,
            expected_model="BAAI/bge-small-en-v1.5",
            expected_index="duediligence-chunks",
            reported={
                "profile": "finetuned",
                "model": "BAAI/bge-small-en-v1.5",
                "index": "duediligence-chunks",
            },
        )
        assert len(problems) == 1
        assert "profile" in problems[0]


class TestDivergence:
    def test_identical_lists_agree_on_members_and_order(self, script):
        result = script.divergence(["a", "b"], ["a", "b"])
        assert result["same_members"] and result["same_order"]

    def test_a_reordering_keeps_members_but_loses_order(self, script):
        """The fine-tune's visible effect through fusion is reordering, not
        different documents — a check that only compared sets would call the
        two arms identical."""
        result = script.divergence(["a", "b"], ["b", "a"])
        assert result["same_members"]
        assert not result["same_order"]

    def test_different_members_are_named_on_the_side_they_appear(self, script):
        result = script.divergence(["a", "b"], ["a", "c"])
        assert not result["same_members"]
        assert result["only_in_base"] == ["b"]
        assert result["only_in_candidate"] == ["c"]


class TestProfileEnv:
    def test_it_sets_the_variable_a_deployment_would_set(self, script, monkeypatch):
        monkeypatch.delenv(PROFILE_ENV_VAR, raising=False)
        with script.profile_env("finetuned"):
            assert os.environ[PROFILE_ENV_VAR] == "finetuned"
        assert PROFILE_ENV_VAR not in os.environ

    def test_the_base_arm_clears_an_inherited_value(self, script, monkeypatch):
        """A shell that already exported the profile would otherwise make the
        baseline arm a second fine-tuned run, and the comparison would be an
        index against itself."""
        monkeypatch.setenv(PROFILE_ENV_VAR, "finetuned")
        with script.profile_env(None):
            assert PROFILE_ENV_VAR not in os.environ
        assert os.environ[PROFILE_ENV_VAR] == "finetuned"

    def test_it_restores_the_previous_value_after_an_error(self, script, monkeypatch):
        monkeypatch.setenv(PROFILE_ENV_VAR, "original")
        with pytest.raises(RuntimeError), script.profile_env("finetuned"):
            raise RuntimeError("boom")
        assert os.environ[PROFILE_ENV_VAR] == "original"


class TestArmNaming:
    def test_a_profile_called_base_is_rejected_rather_than_overwriting_the_baseline(
        self, script, monkeypatch, capsys
    ):
        """The arms are keyed by name and "base" is the no-profile arm. A
        profile of the same name would collapse both keys onto one dict, and
        every comparison would then be that arm against itself — passing, and
        meaningless."""
        monkeypatch.setattr(sys, "argv", ["verify_served_profile.py", "--profile", "base"])
        with pytest.raises(SystemExit) as exit_info:
            script.main()
        assert exit_info.value.code == 2
        assert "base" in capsys.readouterr().err
