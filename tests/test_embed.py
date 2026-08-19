"""The embedder's conventions, and the seam where a backend plugs into them.

`index/embed.py` owns three things no execution backend is allowed to
redefine: BGE's query-side instruction prefix, unit-norm vectors, and the
384-dimension the index mapping is built for. All three fail *silently* when
broken — you get vectors, you get a ranking, and it is a worse one — so they
are asserted at construction against whichever backend loaded, and pinned
here against a fake one.

The ONNX backend's own seams live in `tests/test_onnx_embed.py`.
"""
from __future__ import annotations

import numpy as np
import pytest

from duediligence.index.embed import (
    BACKEND_ENV_VAR,
    EMBEDDING_DIMENSION,
    QUERY_INSTRUCTION,
    ChunkEmbedder,
    assert_unit_norm,
    resolve_backend,
)


class TestResolveBackend:
    def test_defaults_to_torch(self, monkeypatch):
        monkeypatch.delenv(BACKEND_ENV_VAR, raising=False)
        assert resolve_backend() == "torch"

    def test_environment_selects_a_backend(self, monkeypatch):
        monkeypatch.setenv(BACKEND_ENV_VAR, "onnx-int8")
        assert resolve_backend() == "onnx-int8"

    def test_an_explicit_argument_beats_the_environment(self, monkeypatch):
        monkeypatch.setenv(BACKEND_ENV_VAR, "onnx-int8")
        assert resolve_backend("torch") == "torch"

    def test_an_unknown_backend_raises_rather_than_falling_back(self, monkeypatch):
        monkeypatch.delenv(BACKEND_ENV_VAR, raising=False)
        # A fallback here would report PyTorch's latency under an ONNX label.
        with pytest.raises(ValueError, match="unknown embedding backend"):
            resolve_backend("onnxx")

    def test_an_unknown_backend_in_the_environment_also_raises(self, monkeypatch):
        monkeypatch.setenv(BACKEND_ENV_VAR, "tensorrt")
        with pytest.raises(ValueError, match="tensorrt"):
            resolve_backend()


class FakeEncoder:
    """A backend that encodes deterministically from the text itself, so a
    test can tell which text produced which row."""

    describe = "fake"

    def __init__(self, *, dimension: int = EMBEDDING_DIMENSION, normalize: bool = True) -> None:
        self.dimension = dimension
        self.normalize = normalize
        self.calls: list[list[str]] = []

    def encode(self, texts, *, show_progress: bool = False) -> np.ndarray:
        texts = list(texts)
        self.calls.append(texts)
        vectors = np.array(
            [[float(len(text))] + [1.0] * (self.dimension - 1) for text in texts],
            dtype=np.float32,
        )
        if self.normalize:
            vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors


class TestBackendContract:
    """Whatever the backend, the same three guarantees hold — they are the
    ones the index depends on and none of them fail loudly on their own."""

    def test_queries_take_the_instruction_prefix_and_passages_do_not(self):
        encoder = FakeEncoder()
        embedder = ChunkEmbedder("fake-model", encoder=encoder)
        encoder.calls.clear()

        embedder.embed_queries(["net income"])
        embedder.embed_passages(["net income"])

        assert encoder.calls[0] == [QUERY_INSTRUCTION + "net income"]
        assert encoder.calls[1] == ["net income"]

    def test_a_wrong_dimension_backend_is_rejected_at_construction(self):
        with pytest.raises(ValueError, match="768-dim"):
            ChunkEmbedder("fake-model", encoder=FakeEncoder(dimension=768))

    def test_an_un_normalized_backend_is_rejected_at_construction(self):
        # Un-normalized vectors in a cosine-scored field rank on magnitude.
        with pytest.raises(ValueError, match="norm"):
            ChunkEmbedder("fake-model", encoder=FakeEncoder(normalize=False))

    def test_the_backend_actually_loaded_is_reported(self, monkeypatch):
        monkeypatch.setenv(BACKEND_ENV_VAR, "onnx-int8")
        embedder = ChunkEmbedder("fake-model", encoder=FakeEncoder())
        assert embedder.backend == "onnx-int8"
        assert embedder.describe == "fake"

    def test_empty_input_still_returns_the_index_width(self):
        embedder = ChunkEmbedder("fake-model", encoder=FakeEncoder())
        assert embedder.embed_passages([]).shape == (0, EMBEDDING_DIMENSION)
        assert embedder.embed_queries([]).shape == (0, EMBEDDING_DIMENSION)


class FakeSentenceTransformer:
    """Stands in for the real model so the PyTorch backend's conventions can
    be checked without loading 130MB of weights."""

    def __init__(self, model_name, device=None):
        self.model_name = model_name
        self.device = device
        self.calls: list[dict] = []

    def encode(self, texts, **kwargs):
        self.calls.append({"texts": list(texts), **kwargs})
        return np.tile(
            np.eye(1, EMBEDDING_DIMENSION, dtype=np.float64), (len(list(texts)), 1)
        )


class TestTorchEncoder:
    """The default backend is a backend too, and it has the same contract.

    Worth pinning rather than assuming: these two keyword arguments are the
    difference between vectors a cosine-scored k-NN field ranks correctly and
    vectors it ranks by magnitude, and neither would raise.
    """

    @pytest.fixture
    def fake_module(self, monkeypatch):
        """Inject a fake ``sentence_transformers`` so the hermetic unit suite
        never loads 130MB of weights to check two keyword arguments."""
        import sys
        import types

        module = types.ModuleType("sentence_transformers")
        module.SentenceTransformer = FakeSentenceTransformer
        monkeypatch.setitem(sys.modules, "sentence_transformers", module)
        return module

    def test_it_normalizes_and_returns_float32(self, fake_module, monkeypatch):
        from duediligence.index import embed as embed_module

        monkeypatch.setattr(embed_module, "resolve_device", lambda preferred=None: "cpu")
        embedder = ChunkEmbedder("fake-model", backend="torch", batch_size=7)

        vectors = embedder.embed_passages(["one", "two"])
        call = embedder.encoder.model.calls[-1]
        assert call["normalize_embeddings"] is True
        assert call["batch_size"] == 7
        assert vectors.dtype == np.float32

    def test_the_device_it_loaded_on_is_reported(self, fake_module, monkeypatch):
        from duediligence.index import embed as embed_module

        monkeypatch.setattr(embed_module, "resolve_device", lambda preferred=None: "cpu")
        embedder = ChunkEmbedder("fake-model", backend="torch")
        assert embedder.device == "cpu"
        assert embedder.describe == "torch:cpu"


class TestAssertUnitNorm:
    """One implementation, shared by the load-time probe and the post-export
    check — a second idea of "is this normalized" is how the two code paths
    would come to disagree."""

    def test_unit_vectors_pass(self):
        assert_unit_norm(np.eye(3, dtype=np.float32), context="probe")

    def test_a_short_vector_names_its_norm_and_the_consequence(self):
        with pytest.raises(ValueError, match="rank on magnitude"):
            assert_unit_norm(np.full((1, 4), 0.1, dtype=np.float32), context="probe")

    def test_one_bad_row_among_good_ones_still_fails(self):
        vectors = np.eye(3, dtype=np.float32)
        vectors[2] *= 4.0
        with pytest.raises(ValueError, match="4.000000"):
            assert_unit_norm(vectors, context="probe")


class TestDeviceIsNotSilentlyDropped:
    def test_a_torch_device_on_an_onnx_backend_raises(self):
        # The ONNX sessions run on the CPU execution provider. Ignoring
        # device="mps" would let a caller believe it measured GPU execution.
        with pytest.raises(ValueError, match="cannot honour it"):
            ChunkEmbedder("fake-model", backend="onnx", device="mps")

    def test_no_device_is_fine_on_any_backend(self):
        embedder = ChunkEmbedder("fake-model", backend="onnx-int8", encoder=FakeEncoder())
        assert embedder.device is None
