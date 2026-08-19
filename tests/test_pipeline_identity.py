"""What the pipeline says it is serving.

An embedding model and its index are a matched pair. A process holding the
wrong one does not error: cosine similarity across two incompatible vector
spaces is still a number, so it returns plausible rankings built on nothing.
The only defence at serving time is for the process to state which model it
actually loaded, so the mismatch is observable rather than invisible.

These tests construct the pipeline without ``__init__`` on purpose — a real
one loads two transformer models and needs a live OpenSearch, and the
property under test is exactly the one that must not go through config.
"""
from __future__ import annotations

from duediligence.config import Config, ModelsConfig, OpenSearchConfig
from duediligence.pipeline import DueDiligencePipeline


class _StubEmbedder:
    def __init__(self, model_name: str, backend: str | None = None) -> None:
        self.model_name = model_name
        if backend is not None:
            self.backend = backend


def _pipeline(
    *, loaded: str, configured: str, profile: str | None, backend: str | None = None
) -> DueDiligencePipeline:
    pipeline = object.__new__(DueDiligencePipeline)
    pipeline.config = Config(
        models=ModelsConfig(configured, "reranker", "gen", "vision"),
        opensearch=OpenSearchConfig("duediligence-chunks", "local", ""),
        profile=profile,
    )
    pipeline.embedder = _StubEmbedder(loaded, backend)
    return pipeline


class TestServedIdentity:
    def test_model_name_comes_from_the_loaded_embedder_not_from_config(self):
        """Reading config would only echo what was asked for. The whole point
        is to report what was built, so the two disagreeing is visible."""
        pipeline = _pipeline(
            loaded="models/bge-small-duediligence",
            configured="BAAI/bge-small-en-v1.5",
            profile=None,
        )
        assert pipeline.model_name == "models/bge-small-duediligence"

    def test_profile_comes_from_the_loaded_config(self):
        pipeline = _pipeline(loaded="m", configured="m", profile="finetuned")
        assert pipeline.profile == "finetuned"

    def test_profile_is_none_when_no_profile_was_selected(self):
        pipeline = _pipeline(loaded="m", configured="m", profile=None)
        assert pipeline.profile is None


class TestServedBackend:
    """The same weights on a different runtime are still a different thing to
    serve: INT8 measurably changes what comes back (#13). A process must say
    which one it loaded, not which one was configured."""

    def test_backend_comes_from_the_loaded_embedder(self):
        pipeline = _pipeline(loaded="m", configured="m", profile=None, backend="onnx-int8")
        assert pipeline.backend == "onnx-int8"

    def test_an_embedder_without_a_backend_reports_the_default(self):
        # Stub embedders elsewhere in this suite predate backends; reporting
        # "torch" for them is right, because that is what they are.
        pipeline = _pipeline(loaded="m", configured="m", profile=None)
        assert pipeline.backend == "torch"
