from __future__ import annotations

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
