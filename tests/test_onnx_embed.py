"""The ONNX backend's seams: selection, batching, and the interface contract.

#13 adds a second and third execution backend for the same weights. The risk
it introduces is not that the export fails loudly — it is that an optimised
backend returns vectors that are the wrong width, the wrong magnitude, or in
the wrong *order*, all of which produce a ranking rather than an error and so
travel silently into every retrieval number downstream.

These tests drive the parts that hold without loading a model, which is all of
the ordering and contract logic. The parts that need real weights (does the
exported graph reproduce PyTorch's vectors, and what does INT8 cost in recall)
are checked by ``export_onnx`` itself and measured by
``scripts/benchmark_onnx.py`` — the unit suite stays hermetic.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from duediligence.index.onnx_embed import (
    INT8_MODEL_FILENAME,
    ONNX_MODEL_FILENAME,
    OnnxEncoder,
    onnx_export_dir,
    sorted_batches,
)


class TestExportDirectory:
    def test_a_hub_id_and_a_local_path_land_in_distinct_directories(self):
        assert onnx_export_dir("BAAI/bge-small-en-v1.5") != onnx_export_dir(
            "models/bge-small-duediligence"
        )

    def test_an_export_never_lands_inside_the_checkpoint_it_came_from(self):
        # The fine-tuned checkpoint is verified file-by-file against a digest
        # manifest, which reports any file it does not list. An export written
        # into that directory would turn a passing provenance check into a
        # failing one.
        checkpoint = Path("models/bge-small-duediligence").resolve()
        assert checkpoint not in onnx_export_dir("models/bge-small-duediligence").resolve().parents


class TestSortedBatches:
    def test_every_index_appears_exactly_once(self):
        texts = ["a" * n for n in (5, 1, 9, 3, 7)]
        flat = [i for batch in sorted_batches(texts, 2) for i in batch]
        assert sorted(flat) == list(range(len(texts)))

    def test_batches_group_similar_lengths(self):
        texts = ["a", "bbbb", "cc", "ddddddd"]
        assert sorted_batches(texts, 2) == [[3, 1], [2, 0]]

    def test_the_last_batch_is_short_rather_than_padded(self):
        assert [len(b) for b in sorted_batches(["x"] * 5, 2)] == [2, 2, 1]

    def test_no_texts_means_no_batches(self):
        assert sorted_batches([], 4) == []

    def test_a_zero_batch_size_raises_rather_than_looping_forever(self):
        with pytest.raises(ValueError, match="batch_size"):
            sorted_batches(["a"], 0)


class RecordingOnnxEncoder(OnnxEncoder):
    """``OnnxEncoder`` with the session replaced — everything except the
    forward pass, which is the part that needs 130MB of weights."""

    def __init__(self, batch_size: int) -> None:
        self.batch_size = batch_size
        self.max_seq_length = 512
        self.quantized = False
        self.model_name = "fake-model"
        self.model_path = Path("nowhere")

    def _forward(self, texts):
        return np.array([[float(len(t)), 0.0] for t in texts], dtype=np.float32)


class TestOnnxEncodeOrdering:
    def test_vectors_come_back_in_the_caller_order_not_the_batch_order(self):
        # Length-sorted batching is what makes the ONNX backend comparable to
        # sentence-transformers; scattering the results back is what keeps it
        # correct. Getting this wrong mis-pairs every chunk with its embedding
        # and still indexes cleanly.
        texts = ["aaa", "a", "aaaaaaa", "aa"]
        vectors = RecordingOnnxEncoder(batch_size=2).encode(texts)
        assert [v[0] for v in vectors] == [3.0, 1.0, 7.0, 2.0]

    def test_no_texts_needs_no_session_call(self):
        assert RecordingOnnxEncoder(batch_size=2).encode([]).shape == (0, 0)


class TestMissingExport:
    def test_a_missing_export_names_the_command_that_produces_it(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="scripts/export_onnx.py"):
            OnnxEncoder("fake-model", quantized=False, batch_size=8, export_dir=tmp_path)

    def test_the_two_variants_are_distinct_files(self, tmp_path):
        (tmp_path / ONNX_MODEL_FILENAME).write_bytes(b"")
        with pytest.raises(FileNotFoundError, match=INT8_MODEL_FILENAME):
            OnnxEncoder("fake-model", quantized=True, batch_size=8, export_dir=tmp_path)


