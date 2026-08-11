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
