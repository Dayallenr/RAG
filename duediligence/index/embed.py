"""
Dense embeddings for chunk text and queries — BAAI/bge-small-en-v1.5,
self-hosted. The model name comes from config, so a fine-tuned
checkpoint can be swapped in without touching this module.

Two details that are easy to get wrong and silently cost retrieval quality
rather than raising an error:

1. **BGE is an asymmetric model: queries take an instruction prefix,
   passages do not.** The model card specifies
   "Represent this sentence for searching relevant passages: " prepended to
   the *query* side only. Embedding both sides identically still "works" —
   you get vectors, you get a ranking, nothing crashes — it just retrieves
   measurably worse. Passage and query embedding are therefore separate
   methods here rather than one ``encode`` with a flag callers can forget.

2. **Vectors must be normalized**, because the index scores with cosine
   similarity (see ``opensearch_client.py``). ``normalize_embeddings=True``
   is set in one place here so no caller can index un-normalized vectors
   into a cosine-scored field.

The model is 384-dimensional and ~33M parameters — small enough to embed
the whole ~39k-chunk corpus on the user's Mac in minutes on MPS, which is
the whole reason it was chosen over a larger embedding model.

The same weights run on more than one stack: ``DUEDILIGENCE_EMBEDDING_BACKEND``
selects PyTorch (the default, and what every number outside ``results/onnx/``
was produced with) or an exported ONNX graph, fp32 or INT8. The backend only
turns text into vectors — both conventions above are enforced here, once, for
whichever backend is loaded, and asserted at construction rather than trusted.
"""
from __future__ import annotations

import logging
import os
from collections.abc import Iterable
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

__all__ = [
    "BACKENDS",
    "BACKEND_ENV_VAR",
    "assert_unit_norm",
    "EMBEDDING_DIMENSION",
    "QUERY_INSTRUCTION",
    "ChunkEmbedder",
    "resolve_backend",
    "resolve_device",
]

# bge-small-en-v1.5's hidden size. Asserted against the loaded model in
# ``ChunkEmbedder.__init__`` rather than trusted — the index mapping is
# built from this constant, and a mismatch would only surface as a rejected
# bulk request thousands of documents into a run.
EMBEDDING_DIMENSION = 384

# Query-side instruction prefix from the bge-small-en-v1.5 model card.
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "

_DEFAULT_BATCH_SIZE = 128

#: Execution backends for the same weights. "torch" is sentence-transformers
#: on the fastest local device; the other two are an exported ONNX graph, fp32
#: and dynamically quantised to INT8 (``index/onnx_embed.py``).
BACKENDS = ("torch", "onnx", "onnx-int8")

#: Selects a backend without a code change, following the precedent set by
#: DUEDILIGENCE_CONFIG_PROFILE and the two OpenSearch overrides: every caller
#: in this repository constructs its embedder as
#: ``ChunkEmbedder(config.models.embedding_model)``, so a backend that had to
#: be passed as an argument could not be switched in a running service
#: without editing each of them.
BACKEND_ENV_VAR = "DUEDILIGENCE_EMBEDDING_BACKEND"


def resolve_backend(preferred: str | None = None) -> str:
    """Pick the execution backend: explicit argument, else the environment,
    else PyTorch. An unknown name raises rather than falling back — a silent
    fallback would report PyTorch latencies under an ONNX label."""
    backend = preferred or os.environ.get(BACKEND_ENV_VAR) or "torch"
    if backend not in BACKENDS:
        raise ValueError(
            f"unknown embedding backend {backend!r}; available backends: {list(BACKENDS)}"
        )
    return backend


#: How far a vector's norm may sit from 1.0 before it is treated as broken.
#: Loose enough for float32 round-trips through three different runtimes,
#: tight enough that an un-normalized vector cannot pass.
_NORM_TOLERANCE = 1e-3


def assert_unit_norm(vectors: np.ndarray, *, context: str) -> None:
    """Raise unless every vector is unit length.

    One implementation, used by both the load-time backend probe and the
    post-export check in ``onnx_embed.py``: the k-NN field is scored by cosine
    similarity, so un-normalized vectors rank by magnitude instead — a wrong
    ranking rather than an error, from either code path.
    """
    norms = np.linalg.norm(vectors, axis=1)
    worst = float(np.abs(norms - 1.0).max())
    if worst > _NORM_TOLERANCE:
        raise ValueError(
            f"{context} returns vectors of norm {float(norms[np.abs(norms - 1.0).argmax()]):.6f}; "
            "the k-NN field is scored by cosine similarity and would rank on magnitude."
        )


def resolve_device(preferred: str | None = None) -> str:
    """Pick the fastest available torch device: explicit choice, else Apple
    Silicon's MPS, else CPU. CUDA is checked too so this doesn't have to
    change if the corpus is ever embedded on a rented GPU box."""
    if preferred:
        return preferred

    import torch

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class _TorchEncoder:
    """sentence-transformers on the fastest local device — the default, and
    the backend every number outside ``results/onnx/`` was produced with."""

    def __init__(self, model_name: str, *, device: str | None, batch_size: int) -> None:
        from sentence_transformers import SentenceTransformer

        self.device = resolve_device(device)
        self.batch_size = batch_size
        logger.info("loading embedding model %s on %s", model_name, self.device)
        self.model = SentenceTransformer(model_name, device=self.device)
        self.describe = f"torch:{self.device}"

    def encode(self, texts: list[str], *, show_progress: bool = False) -> np.ndarray:
        return self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        ).astype(np.float32)


class ChunkEmbedder:
    """This project's fixed encoding conventions (query prefix, normalization,
    dimension check) over an interchangeable execution backend.

    The conventions live here and the backend only turns text into vectors, so
    an optimised runtime cannot quietly drop the query prefix or return
    un-normalized vectors — both of which retrieve worse without raising.
    Every convention is therefore asserted once, at construction, against
    whatever backend was selected: see ``_assert_backend_contract``.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        *,
        device: str | None = None,
        batch_size: int = _DEFAULT_BATCH_SIZE,
        backend: str | None = None,
        encoder: Any | None = None,
    ) -> None:
        self.model_name = model_name
        self.backend = resolve_backend(backend)

        # A torch device on an ONNX backend is not a no-op to ignore: the ONNX
        # sessions here are built with the CPU execution provider, so silently
        # dropping ``device="mps"`` would let a caller believe it measured GPU
        # execution. resolve_backend refuses an unknown backend rather than
        # falling back for the same reason.
        if device is not None and self.backend != "torch":
            raise ValueError(
                f"device={device!r} was requested with backend {self.backend!r}, which "
                "runs on the CPU execution provider and cannot honour it. Drop the "
                "device, or use the torch backend."
            )

        if encoder is not None:
            # Injected for tests: constructing a real backend loads ~130MB of
            # weights, which the hermetic unit suite deliberately never does.
            self.encoder = encoder
        elif self.backend == "torch":
            self.encoder = _TorchEncoder(model_name, device=device, batch_size=batch_size)
        else:
            from duediligence.index.onnx_embed import OnnxEncoder

            self.encoder = OnnxEncoder(
                model_name,
                quantized=self.backend == "onnx-int8",
                batch_size=batch_size,
            )

        #: The torch device, or None for a backend that does not have one.
        #: Reported by the health endpoints alongside the model, so a running
        #: process says what it actually loaded rather than what was asked for.
        self.device = getattr(self.encoder, "device", None)
        self._assert_backend_contract()

    def _assert_backend_contract(self) -> None:
        """Encode one probe and check the two properties the index mapping
        depends on: the vector width it was built for, and unit norm for a
        cosine-scored field.

        Cheap (one short forward pass at startup) and it runs on every
        backend, which is the point: a broken export returns vectors of the
        wrong width or the wrong magnitude, and both produce rankings rather
        than errors. The third convention — query and passage encoding staying
        distinct — cannot be settled by one probe and is measured per backend
        by ``scripts/benchmark_onnx.py``.
        """
        probe = self.encoder.encode([QUERY_INSTRUCTION + "net income"])
        if probe.shape[1] != EMBEDDING_DIMENSION:
            raise ValueError(
                f"{self.model_name} on backend {self.backend!r} produces "
                f"{probe.shape[1]}-dim vectors but the index mapping is built for "
                f"{EMBEDDING_DIMENSION}; update EMBEDDING_DIMENSION and recreate the index."
            )
        assert_unit_norm(probe, context=f"backend {self.backend!r}")

    @property
    def describe(self) -> str:
        """What is actually executing, for a report or a health endpoint."""
        return getattr(self.encoder, "describe", self.backend)

    def embed_passages(self, texts: Iterable[str], *, show_progress: bool = False) -> np.ndarray:
        """Embed chunk text for indexing — no instruction prefix."""
        texts = list(texts)
        if not texts:
            return np.empty((0, EMBEDDING_DIMENSION), dtype=np.float32)
        return self.encoder.encode(texts, show_progress=show_progress)

    def embed_queries(self, queries: Iterable[str]) -> np.ndarray:
        """Embed search queries — with BGE's query instruction prefix."""
        queries = list(queries)
        if not queries:
            return np.empty((0, EMBEDDING_DIMENSION), dtype=np.float32)
        return self.encoder.encode([QUERY_INSTRUCTION + query for query in queries])

    def embed_query(self, query: str) -> list[float]:
        """Single-query convenience returning a plain list, the shape the
        OpenSearch k-NN query body wants."""
        return self.embed_queries([query])[0].tolist()
