"""
Dense embeddings for chunk text and queries — BAAI/bge-small-en-v1.5,
self-hosted and inference-only (no fine-tuning, see CLAUDE.md).

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
"""
from __future__ import annotations

import logging
from collections.abc import Iterable

import numpy as np

logger = logging.getLogger(__name__)

__all__ = ["EMBEDDING_DIMENSION", "QUERY_INSTRUCTION", "ChunkEmbedder", "resolve_device"]

# bge-small-en-v1.5's hidden size. Asserted against the loaded model in
# ``ChunkEmbedder.__init__`` rather than trusted — the index mapping is
# built from this constant, and a mismatch would only surface as a rejected
# bulk request thousands of documents into a run.
EMBEDDING_DIMENSION = 384

# Query-side instruction prefix from the bge-small-en-v1.5 model card.
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "

_DEFAULT_BATCH_SIZE = 128


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


class ChunkEmbedder:
    """Wraps a sentence-transformers model with this project's fixed
    encoding conventions (query prefix, normalization, dimension check)."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        *,
        device: str | None = None,
        batch_size: int = _DEFAULT_BATCH_SIZE,
    ) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.device = resolve_device(device)
        self.batch_size = batch_size

        logger.info("loading embedding model %s on %s", model_name, self.device)
        self.model = SentenceTransformer(model_name, device=self.device)

        # sentence-transformers 5.x renamed this method; requirements.txt
        # allows >=3.2.0, where only the old name exists.
        get_dimension = getattr(
            self.model, "get_embedding_dimension", None
        ) or self.model.get_sentence_embedding_dimension
        actual_dimension = get_dimension()
        if actual_dimension != EMBEDDING_DIMENSION:
            raise ValueError(
                f"{model_name} produces {actual_dimension}-dim vectors but the index "
                f"mapping is built for {EMBEDDING_DIMENSION}; update EMBEDDING_DIMENSION "
                f"and recreate the index."
            )

    def embed_passages(self, texts: Iterable[str], *, show_progress: bool = False) -> np.ndarray:
        """Embed chunk text for indexing — no instruction prefix."""
        texts = list(texts)
        if not texts:
            return np.empty((0, EMBEDDING_DIMENSION), dtype=np.float32)
        return self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        ).astype(np.float32)

    def embed_queries(self, queries: Iterable[str]) -> np.ndarray:
        """Embed search queries — with BGE's query instruction prefix."""
        queries = list(queries)
        if not queries:
            return np.empty((0, EMBEDDING_DIMENSION), dtype=np.float32)
        return self.model.encode(
            [QUERY_INSTRUCTION + query for query in queries],
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        ).astype(np.float32)

    def embed_query(self, query: str) -> list[float]:
        """Single-query convenience returning a plain list, the shape the
        OpenSearch k-NN query body wants."""
        return self.embed_queries([query])[0].tolist()
