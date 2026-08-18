"""The fine-tuning script's flags, and whether they reach the trainer.

`scripts/finetune_biencoder.py` cannot be exercised end to end in CI — it needs
a GPU and 27MB of mined splits that are deliberately untracked. What can be
tested is the wiring, and that is where the two flags that silently change what
the run *did* live: `--fp16` and `--gradient-checkpointing`.

**Parsing a flag is not the same as using it**, which is why these tests assert
against the `TrainingArguments` object rather than the parsed namespace. Drop
the `gradient_checkpointing=` line from `build_training_arguments` and a test
reading `args.gradient_checkpointing` still passes, while the run trains without
it — and, before the report started reading the trainer instead of the parsed
args, `results/training/report.json` would still have recorded it as enabled.
That is a run that quietly did not do what was asked, reported as if it had.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "finetune_biencoder.py"


@pytest.fixture(scope="module")
def script():
    """Import the script as a module. Its heavy imports (torch,
    sentence-transformers, datasets) are inside ``main``, so this stays cheap."""
    spec = importlib.util.spec_from_file_location("finetune_biencoder", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_gradient_checkpointing_defaults_off(script):
    args = script.build_parser().parse_args([])
    assert args.gradient_checkpointing is False


def test_gradient_checkpointing_is_settable(script):
    args = script.build_parser().parse_args(["--gradient-checkpointing"])
    assert args.gradient_checkpointing is True


def test_fp16_defaults_off(script):
    assert script.build_parser().parse_args([]).fp16 is False


@pytest.fixture(scope="module")
def training_arguments(script, tmp_path_factory):
    """Build the real `TrainingArguments` the script would hand the trainer.

    Imports sentence-transformers, so it is built once per module and reused.
    """

    def build(argv):
        return script.build_training_arguments(
            script.build_parser().parse_args(argv),
            output=tmp_path_factory.mktemp("out"),
            fp16=False,
            report_to=[],
        )

    return build


def test_gradient_checkpointing_reaches_the_trainer(training_arguments):
    assert training_arguments(["--gradient-checkpointing"]).gradient_checkpointing is True


def test_gradient_checkpointing_off_by_default_in_the_trainer(training_arguments):
    assert training_arguments([]).gradient_checkpointing is False


def test_fp16_is_the_resolved_value_not_the_parsed_one(training_arguments):
    """`main` downgrades `--fp16` to False off CUDA and passes the *resolved*
    value here. Asking for fp16 must not produce fp16 arguments on its own."""
    assert training_arguments(["--fp16"]).fp16 is False


def test_batch_size_reaches_the_trainer(training_arguments):
    assert training_arguments(["--batch-size", "8"]).per_device_train_batch_size == 8


def test_default_output_matches_the_finetuned_profile(script):
    """The profile names where a local run puts the checkpoint. If the script's
    default `--out` and the profile's `embedding_model` drift apart, the profile
    points at a directory training never wrote, and the failure is a confusing
    'model not found' rather than an obvious mismatch."""
    import yaml

    profile = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "config/profiles/finetuned.yaml").read_text()
    )
    assert profile["models"]["embedding_model"] == script.build_parser().parse_args([]).out
