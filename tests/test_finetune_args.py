"""The fine-tuning script's flags.

`scripts/finetune_biencoder.py` cannot be exercised end to end in CI — it needs
a GPU and 27MB of mined splits that are deliberately untracked. Its argument
surface can be, and that is where the two flags that silently change what the
run *did* live: `--fp16` and `--gradient-checkpointing`. A run that quietly
trained without the memory setting it was asked for is the failure this guards
against, the same reasoning that makes the script refuse `--fp16` off CUDA
rather than let the trainer drop it.
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
