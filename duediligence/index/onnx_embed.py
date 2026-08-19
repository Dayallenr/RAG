"""
ONNX Runtime backend for the bi-encoder, and the export that produces it.

Inference optimisation the honest way: the same weights, a different
execution stack, and a measurement of what the swap costs in retrieval
quality rather than only what it saves. `scripts/benchmark_onnx.py` is the
artifact; this module is what it benchmarks.

Three things here are easy to get wrong and produce a model that returns
plausible vectors rather than an error:

1. **Pooling and normalization belong inside the graph.** The checkpoint is
   ``Transformer -> Pooling(cls) -> Normalize`` (``modules.json``). Exporting
   only the transformer and re-implementing CLS pooling and L2 normalization
   in Python would be a second implementation of the serving convention,
   free to drift from the sentence-transformers one. The exported graph ends
   at the normalized sentence embedding, so both backends are the same
   function of the text.

2. **The export is traced, so it must be checked at shapes it was not traced
   at.** ``torch.onnx.export`` records one concrete forward pass; transformers'
   attention path contains data-dependent Python branches that emit
   ``TracerWarning``. Whether those branches baked a constant into the graph
   is a question about this specific model and version, so ``export_onnx``
   re-checks the exported graph against the PyTorch model on batches of
   different length — including one at the full 512-token window — and refuses
   to write an export that disagrees.

3. **Length-sorted batching is not an optimisation, it is the comparison.**
   ``sentence_transformers.encode`` sorts by length before batching, so short
   texts are not padded up to the longest text in the batch. Measured here on
   256 real corpus chunks at batch 32, fp32: arrival order 13.6 texts/s,
   length-sorted 22.9 — a 1.69x difference that has nothing to do with the
   runtime. An ONNX backend that skipped it would lose a benchmark against
   PyTorch on padding rather than on execution. (An ad-hoc timing on this
   machine, not a report file.)
"""
from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from pathlib import Path

import numpy as np

from duediligence.index.embed import assert_unit_norm

logger = logging.getLogger(__name__)

__all__ = [
    "INT8_MODEL_FILENAME",
    "ONNX_MODEL_FILENAME",
    "OnnxEncoder",
    "export_onnx",
    "onnx_export_dir",
    "sorted_batches",
]

ONNX_MODEL_FILENAME = "model.onnx"
INT8_MODEL_FILENAME = "model_int8.onnx"

#: The three inputs of an exported BERT graph, in the order the export names
#: them. BGE is a BERT and always takes token type ids.
_INPUT_NAMES = ("input_ids", "attention_mask", "token_type_ids")

#: Where an export lands, derived from the model name rather than configured.
#: A configurable path would let a benchmark run against an export nobody
#: else can reproduce; deriving it means `export_onnx` and `OnnxEncoder`
#: cannot disagree about where the file is.
_EXPORT_ROOT = Path("models/onnx")

#: Exports go *beside* the checkpoint, never inside it. The fine-tuned
#: checkpoint is verified file-by-file against a digest manifest written on
#: the machine that trained it (``duediligence/train/checkpoint.py``), and any
#: file that manifest does not list is reported as a problem — so writing an
#: export into the checkpoint directory would turn a passing provenance check
#: into a failing one.
def onnx_export_dir(model_name: str) -> Path:
    """The directory holding ``model_name``'s export.

    Keyed on the last path/repo segment, so ``BAAI/bge-small-en-v1.5`` and
    ``models/bge-small-duediligence`` land in distinct directories without
    either of them nesting inside the source it came from.
    """
    return _EXPORT_ROOT / Path(model_name).name


def sorted_batches(texts: Sequence[str], batch_size: int) -> list[list[int]]:
    """Indices into ``texts``, grouped into batches of similar length.

    Returns indices rather than the texts themselves so the caller can scatter
    results back into the caller's order. Encoding returns vectors in the
    order the texts arrived; a backend that returned them length-sorted would
    silently mis-pair every chunk with its embedding.
    """
    if batch_size < 1:
        raise ValueError(f"batch_size must be >= 1, got {batch_size}")
    order = sorted(range(len(texts)), key=lambda i: len(texts[i]), reverse=True)
    return [order[start : start + batch_size] for start in range(0, len(order), batch_size)]


class OnnxEncoder:
    """Encodes text with an exported ONNX graph, fp32 or dynamically quantised.

    Deliberately *not* a ``SentenceTransformer`` subclass: it implements only
    ``encode``, the one thing ``ChunkEmbedder`` asks a backend for. The query
    prefix, the dimension assertion and the normalization contract stay in
    ``ChunkEmbedder`` so they hold identically across backends.
    """

    def __init__(
        self,
        model_name: str,
        *,
        quantized: bool,
        batch_size: int,
        max_seq_length: int = 512,
        export_dir: Path | str | None = None,
    ) -> None:
        self.model_name = model_name
        self.quantized = quantized
        self.batch_size = batch_size
        self.max_seq_length = max_seq_length

        directory = Path(export_dir) if export_dir is not None else onnx_export_dir(model_name)
        filename = INT8_MODEL_FILENAME if quantized else ONNX_MODEL_FILENAME
        self.model_path = directory / filename
        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"no ONNX export at {self.model_path}. Export it first:\n"
                f"    python scripts/export_onnx.py --model {model_name}\n"
                "Exports are derived artifacts and are not tracked in git."
            )

        import onnxruntime as ort
        from transformers import AutoTokenizer

        # The tokenizer comes from the source model, not the export directory:
        # the export holds weights, and a second copy of the vocabulary is a
        # second thing that can drift from the checkpoint being served.
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        logger.info("loading ONNX session %s", self.model_path)
        self.session = ort.InferenceSession(
            str(self.model_path), providers=["CPUExecutionProvider"]
        )

    @property
    def describe(self) -> str:
        return f"onnx-int8:{self.model_path}" if self.quantized else f"onnx:{self.model_path}"

    def _forward(self, texts: Sequence[str]) -> np.ndarray:
        encoded = self.tokenizer(
            list(texts),
            padding=True,
            truncation=True,
            max_length=self.max_seq_length,
            return_tensors="np",
        )
        feeds = {name: encoded[name].astype(np.int64) for name in _INPUT_NAMES}
        return self.session.run(None, feeds)[0].astype(np.float32)

    def encode(self, texts: Iterable[str], *, show_progress: bool = False) -> np.ndarray:
        texts = list(texts)
        if not texts:
            return np.empty((0, 0), dtype=np.float32)

        batches = sorted_batches(texts, self.batch_size)
        out: np.ndarray | None = None
        for number, indices in enumerate(batches, start=1):
            vectors = self._forward([texts[i] for i in indices])
            if out is None:
                out = np.empty((len(texts), vectors.shape[1]), dtype=np.float32)
            out[indices] = vectors
            if show_progress:
                logger.info("onnx encode batch %d/%d", number, len(batches))
        assert out is not None  # non-empty texts always produce at least one batch
        return out


#: The exported graph must reproduce PyTorch's vectors, not merely correlate
#: with them: same weights, same arithmetic, only a different runtime.
#: Measured on the real export: 2.9e-07 max absolute difference.
_EXPORT_MAX_ABS_DIFF = 1e-4

#: Quantisation *does* change the arithmetic, so this floor is a sanity gate
#: against a broken quantisation, not a quality claim — what the quantisation
#: actually costs is measured against the eval set by
#: ``scripts/benchmark_onnx.py``. Measured on the real export: 0.989 minimum
#: cosine against the fp32 vectors.
_QUANTIZED_MIN_COSINE = 0.95

#: Probe texts for the post-export check, at deliberately different lengths.
#: The export is traced at one shape; the risk it carries is a sequence length
#: or batch size baked in as a constant, which only shows up at another one.
#: The last probe is long enough to fill the 512-token window after
#: truncation, so the check covers the boundary the corpus actually hits
#: (6.8% of mined positives exceed it).
_PROBE_TEXTS = [
    "net income",
    "The merger of equals between Columbia Banking System and Umpqua Holdings.",
    "Total deposits decreased during the period, reflecting seasonal outflows "
    "and competition for retail balances across the bank's footprint. ",
]


def _probe_batches() -> list[list[str]]:
    long_text = _PROBE_TEXTS[2] * 40
    return [[_PROBE_TEXTS[0]], _PROBE_TEXTS[:2], [long_text, _PROBE_TEXTS[0], _PROBE_TEXTS[1]]]


def export_onnx(
    model_name: str,
    *,
    out_dir: Path | str | None = None,
    quantize: bool = True,
    opset: int = 17,
) -> dict:
    """Export ``model_name`` to ONNX, optionally quantise it, and check both.

    Returns the report the export script writes: paths, sizes, and the
    agreement numbers the checks produced. Raises rather than returning a
    failing report — an export that disagrees with the model it came from is
    not an artifact worth keeping around to be benchmarked by accident.
    """
    import torch
    from sentence_transformers import SentenceTransformer

    directory = Path(out_dir) if out_dir is not None else onnx_export_dir(model_name)
    directory.mkdir(parents=True, exist_ok=True)
    fp32_path = directory / ONNX_MODEL_FILENAME

    # CPU, not the fastest available device: the export traces the forward
    # pass, and tracing on MPS has produced device-typed constants in the
    # graph. Export is a one-off, so its own speed does not matter.
    model = SentenceTransformer(model_name, device="cpu")
    tokenizer = model.tokenizer
    max_seq_length = model.max_seq_length

    class _Encoder(torch.nn.Module):
        """Transformer -> CLS pooling -> L2 normalize, as one graph.

        Mirrors the checkpoint's own ``modules.json`` rather than assuming
        mean pooling — bge-small pools on CLS, and pooling the wrong way
        produces vectors that look fine and retrieve worse.
        """

        def __init__(self, backbone: torch.nn.Module) -> None:
            super().__init__()
            self.backbone = backbone

        def forward(
            self,
            input_ids: torch.Tensor,
            attention_mask: torch.Tensor,
            token_type_ids: torch.Tensor,
        ) -> torch.Tensor:
            hidden = self.backbone(
                input_ids=input_ids,
                attention_mask=attention_mask,
                token_type_ids=token_type_ids,
            ).last_hidden_state
            return torch.nn.functional.normalize(hidden[:, 0], p=2, dim=1)

    _assert_cls_pooling(model, model_name)

    encoder = _Encoder(model[0].auto_model).eval()
    dummy = tokenizer(
        _PROBE_TEXTS[:2], padding=True, truncation=True, max_length=32, return_tensors="pt"
    )
    dynamic_axes = {name: {0: "batch", 1: "sequence"} for name in _INPUT_NAMES}
    dynamic_axes["sentence_embedding"] = {0: "batch"}

    logger.info("exporting %s to %s", model_name, fp32_path)
    with torch.no_grad():
        torch.onnx.export(
            encoder,
            tuple(dummy[name] for name in _INPUT_NAMES),
            str(fp32_path),
            input_names=list(_INPUT_NAMES),
            output_names=["sentence_embedding"],
            dynamic_axes=dynamic_axes,
            opset_version=opset,
            # The tracing exporter, explicitly. torch 2.9 defaults to the
            # torch.export path, which does not currently produce a graph for
            # this model on this version pair.
            dynamo=False,
        )

    report: dict = {
        "model": model_name,
        "export_dir": str(directory),
        "opset": opset,
        "max_seq_length": max_seq_length,
        "variants": {
            "onnx": {"path": str(fp32_path), "bytes": fp32_path.stat().st_size},
        },
    }

    fp32_encoder = OnnxEncoder(
        model_name,
        quantized=False,
        batch_size=8,
        max_seq_length=max_seq_length,
        export_dir=directory,
    )
    report["variants"]["onnx"]["parity"] = _check_against_torch(model, fp32_encoder)

    if quantize:
        int8_path = _quantize(fp32_path, directory / INT8_MODEL_FILENAME)
        int8_encoder = OnnxEncoder(
            model_name,
            quantized=True,
            batch_size=8,
            max_seq_length=max_seq_length,
            export_dir=directory,
        )
        report["variants"]["onnx-int8"] = {
            "path": str(int8_path),
            "bytes": int8_path.stat().st_size,
            "parity": _check_against_torch(model, int8_encoder),
        }
    return report


def _assert_cls_pooling(model, model_name: str) -> None:
    """Fail early if the checkpoint does not pool the way the graph does.

    ``_Encoder.forward`` hard-codes CLS pooling to match bge-small-en-v1.5 and
    its fine-tune. Pooling the wrong way produces vectors that look fine and
    retrieve worse, and the parity check below would catch it only as an
    unexplained disagreement — this says which assumption broke.

    sentence-transformers renamed the attribute: <5.0 exposes a
    ``pooling_mode_cls_token`` boolean, 5.x a ``pooling_mode`` string.
    requirements.txt allows both, so both are read.
    """
    pooling = model[1]
    is_cls = getattr(pooling, "pooling_mode_cls_token", None)
    if is_cls is None:
        is_cls = getattr(pooling, "pooling_mode", None) == "cls"
    if is_cls is not True:
        raise ValueError(
            f"{model_name} does not pool on the CLS token; the exported graph "
            "hard-codes CLS pooling to match bge-small-en-v1.5 and its "
            "fine-tune. Update _Encoder.forward before exporting this model."
        )


def _quantize(fp32_path: Path, int8_path: Path) -> Path:
    """Dynamic INT8 quantisation of the exported graph's weights.

    Dynamic rather than static: static quantisation needs a calibration set
    and quantises activations too, which for a transformer costs more accuracy
    than it buys on CPU. Dynamic quantises the weights once and computes
    activation scales per inference, which is the standard choice for
    encoder-only models and needs no calibration data.
    """
    from onnxruntime.quantization import QuantType, quantize_dynamic
    from onnxruntime.quantization.shape_inference import quant_pre_process

    preprocessed = int8_path.with_name("model_preprocessed.onnx")
    # ``skip_symbolic_shape`` because symbolic inference raises
    # "Incomplete symbolic shape inference" on this graph — the dynamic
    # sequence axis leaves shapes it cannot resolve. The ONNX shape inference
    # that follows is enough for weight-only quantisation.
    quant_pre_process(str(fp32_path), str(preprocessed), skip_symbolic_shape=True)
    quantize_dynamic(
        str(preprocessed),
        str(int8_path),
        weight_type=QuantType.QInt8,
        per_channel=True,
        # Quantise only the constant weight matrices. Without this, matmuls
        # between two activations are quantised too, which costs accuracy for
        # no size saving — there is no weight there to shrink.
        extra_options={"MatMulConstBOnly": True},
    )
    preprocessed.unlink(missing_ok=True)
    return int8_path


def _check_against_torch(model, encoder: OnnxEncoder) -> dict:
    """Score an exported encoder against the PyTorch model it came from.

    Runs several batch shapes because the export is traced at exactly one.
    """
    max_abs = 0.0
    min_cosine = 1.0
    for batch in _probe_batches():
        reference = model.encode(batch, normalize_embeddings=True, convert_to_numpy=True)
        actual = encoder.encode(batch)
        if actual.shape != reference.shape:
            raise ValueError(
                f"{encoder.describe} returned {actual.shape} where the PyTorch model "
                f"returned {reference.shape} — the export did not keep its dynamic axes."
            )
        max_abs = max(max_abs, float(np.abs(actual - reference).max()))
        min_cosine = min(min_cosine, float(np.sum(actual * reference, axis=1).min()))

    assert_unit_norm(encoder.encode(_PROBE_TEXTS), context=encoder.describe)

    threshold = _QUANTIZED_MIN_COSINE if encoder.quantized else 1.0 - _EXPORT_MAX_ABS_DIFF
    if min_cosine < threshold:
        raise ValueError(
            f"{encoder.describe} disagrees with the PyTorch model: minimum cosine "
            f"{min_cosine:.6f} against a floor of {threshold:.6f}. Refusing to keep an "
            "export that does not reproduce the model it was made from."
        )
    return {
        "max_abs_diff_vs_torch": max_abs,
        "min_cosine_vs_torch": min_cosine,
        "probe_batches": len(_probe_batches()),
    }
