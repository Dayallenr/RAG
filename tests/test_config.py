from __future__ import annotations

from pathlib import Path

import pytest

from duediligence.config import load_config


def test_load_config_reads_all_five_companies():
    config = load_config("config/config.yaml")
    tickers = [c.ticker for c in config.companies]
    assert tickers == ["COLB", "UMPQ", "GBCI", "WSBC", "SSB"]


def test_umpqua_has_explicit_cik_override_for_delisted_ticker():
    config = load_config("config/config.yaml")
    umpqua = config.company("UMPQ")
    assert umpqua.cik == "1077771"


def test_other_companies_have_no_cik_override():
    config = load_config("config/config.yaml")
    assert config.company("COLB").cik is None


def test_company_lookup_missing_ticker_raises():
    config = load_config("config/config.yaml")
    try:
        config.company("NOTREAL")
        raise AssertionError("expected KeyError")
    except KeyError:
        pass


def test_edgar_and_paths_and_models_sections_load():
    config = load_config("config/config.yaml")
    assert config.edgar.rate_limit_per_second == 8
    assert "flamingdj30@gmail.com" in config.edgar.user_agent
    assert config.paths.manifest_path == "data/manifest.json"
    assert config.models.generation_model == "gemini-flash-latest"


class TestEnvironmentOverrides:
    """The YAML endpoint is a developer default; every deployed context
    (Docker network, Kubernetes service DNS, AWS) needs a different one."""

    def test_endpoint_is_overridable_by_env(self, monkeypatch):
        monkeypatch.setenv("DUEDILIGENCE_OPENSEARCH_ENDPOINT", "http://opensearch:9200")
        assert load_config().opensearch.local_endpoint == "http://opensearch:9200"

    def test_backend_is_overridable_by_env(self, monkeypatch):
        monkeypatch.setenv("DUEDILIGENCE_OPENSEARCH_BACKEND", "aws")
        assert load_config().opensearch.backend == "aws"

    def test_yaml_value_is_used_when_env_is_absent(self, monkeypatch):
        monkeypatch.delenv("DUEDILIGENCE_OPENSEARCH_ENDPOINT", raising=False)
        assert load_config().opensearch.local_endpoint == "http://localhost:9200"


class TestConfigProfiles:
    """An alternative embedding model has to be selectable without editing the
    tracked config file, because editing it silently invalidates the baseline
    the alternative is being compared against."""

    def _write_profile(self, tmp_path, name, body):
        base = tmp_path / "config.yaml"
        base.write_text(Path("config/config.yaml").read_text())
        profiles = tmp_path / "profiles"
        profiles.mkdir(exist_ok=True)
        (profiles / f"{name}.yaml").write_text(body)
        return str(base)

    def test_no_profile_reproduces_the_base_configuration(self, tmp_path):
        """Every existing script, test and report path depends on this."""
        base = self._write_profile(tmp_path, "unused", "models:\n  embedding_model: x\n")
        assert load_config(base) == load_config("config/config.yaml")

    def test_a_profile_overlays_only_the_keys_it_declares(self, tmp_path):
        base = self._write_profile(
            tmp_path,
            "finetuned",
            "models:\n"
            "  embedding_model: local/finetuned-bge\n"
            "opensearch:\n"
            "  index_name: duediligence-chunks-finetuned\n",
        )
        config = load_config(base, profile="finetuned")
        assert config.models.embedding_model == "local/finetuned-bge"
        assert config.opensearch.index_name == "duediligence-chunks-finetuned"
        # Untouched keys survive, including siblings inside an overlaid section.
        assert config.models.reranker_model == load_config(base).models.reranker_model
        assert config.opensearch.backend == "local"
        assert [c.ticker for c in config.companies] == ["COLB", "UMPQ", "GBCI", "WSBC", "SSB"]

    def test_an_unknown_profile_raises_rather_than_falling_back(self, tmp_path):
        """A silent fallback produces a report labelled fine-tuned that
        measured the baseline — the exact failure the comparison exists to
        detect."""
        base = self._write_profile(tmp_path, "finetuned", "models: {}\n")
        with pytest.raises(ValueError, match="typo"):
            load_config(base, profile="typo")

    def test_the_error_lists_the_profiles_that_do_exist(self, tmp_path):
        base = self._write_profile(tmp_path, "finetuned", "models: {}\n")
        with pytest.raises(ValueError, match="finetuned"):
            load_config(base, profile="typo")

    def test_changing_the_model_without_the_index_name_raises(self, tmp_path):
        """Two models' vectors in one index scores cosine similarity across
        incompatible spaces: no error, no warning, and no recovery short of
        re-embedding the corpus."""
        base = self._write_profile(
            tmp_path, "halfway", "models:\n  embedding_model: local/finetuned-bge\n"
        )
        with pytest.raises(ValueError, match="index"):
            load_config(base, profile="halfway")

    def test_changing_the_index_name_alone_is_allowed(self, tmp_path):
        """The unsafe direction is only one way round — a second index built
        by the same model is a perfectly ordinary thing to want."""
        base = self._write_profile(
            tmp_path, "scratch", "opensearch:\n  index_name: duediligence-scratch\n"
        )
        config = load_config(base, profile="scratch")
        assert config.opensearch.index_name == "duediligence-scratch"
        assert config.models.embedding_model == load_config(base).models.embedding_model

    def test_a_profile_changing_neither_is_allowed(self, tmp_path):
        base = self._write_profile(
            tmp_path, "quiet", "opensearch:\n  backend: aws\n"
        )
        assert load_config(base, profile="quiet").opensearch.backend == "aws"

    def test_an_environment_variable_selects_a_profile(self, tmp_path, monkeypatch):
        base = self._write_profile(
            tmp_path,
            "fromenv",
            "opensearch:\n  index_name: duediligence-fromenv\n",
        )
        monkeypatch.setenv("DUEDILIGENCE_CONFIG_PROFILE", "fromenv")
        assert load_config(base).opensearch.index_name == "duediligence-fromenv"

    def test_an_explicit_argument_beats_the_environment_variable(self, tmp_path, monkeypatch):
        base = self._write_profile(
            tmp_path, "fromenv", "opensearch:\n  index_name: duediligence-fromenv\n"
        )
        (tmp_path / "profiles" / "explicit.yaml").write_text(
            "opensearch:\n  index_name: duediligence-explicit\n"
        )
        monkeypatch.setenv("DUEDILIGENCE_CONFIG_PROFILE", "fromenv")
        config = load_config(base, profile="explicit")
        assert config.opensearch.index_name == "duediligence-explicit"

    def test_an_empty_environment_variable_means_no_profile(self, tmp_path, monkeypatch):
        base = self._write_profile(tmp_path, "unused", "models: {}\n")
        monkeypatch.setenv("DUEDILIGENCE_CONFIG_PROFILE", "")
        assert load_config(base) == load_config("config/config.yaml")

    def test_environment_endpoint_override_still_applies_under_a_profile(
        self, tmp_path, monkeypatch
    ):
        base = self._write_profile(
            tmp_path, "p", "opensearch:\n  index_name: duediligence-p\n"
        )
        monkeypatch.setenv("DUEDILIGENCE_OPENSEARCH_ENDPOINT", "http://opensearch:9200")
        config = load_config(base, profile="p")
        assert config.opensearch.local_endpoint == "http://opensearch:9200"
        assert config.opensearch.index_name == "duediligence-p"


class TestTrackedProfiles:
    def test_every_tracked_profile_loads(self):
        """A profile that raises on load is only discovered when someone
        reaches for it, which is typically mid-experiment."""
        for path in sorted(Path("config/profiles").glob("*.yaml")):
            load_config(profile=path.stem)
