"""
Typed config loading from config/config.yaml.

One loader, one place that knows the file's shape — everything else in the
project imports a `Config` instance rather than parsing YAML itself.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

__all__ = [
    "CompanyConfig", "Config", "EdgarConfig", "ModelsConfig",
    "OpenSearchConfig", "PathsConfig", "load_config",
]


@dataclass(frozen=True)
class CompanyConfig:
    ticker: str
    name: str
    # SEC's ticker->CIK lookup file only lists currently-active tickers —
    # a company that was acquired and delisted (Umpqua, acquired by Columbia
    # in 2023) drops out of it even though its CIK is permanent and its
    # filing history is still on EDGAR. Set this explicitly for any such
    # company rather than relying on ticker resolution.
    cik: str | None = None


@dataclass(frozen=True)
class EdgarConfig:
    user_agent: str
    data_base_url: str
    archives_base_url: str
    ticker_lookup_url: str
    rate_limit_per_second: float


@dataclass(frozen=True)
class PathsConfig:
    filings_dir: str
    manifest_path: str
    eval_set_path: str
    extraction_eval_set_path: str


@dataclass(frozen=True)
class ModelsConfig:
    embedding_model: str
    reranker_model: str
    generation_model: str
    vision_model: str


@dataclass(frozen=True)
class OpenSearchConfig:
    index_name: str
    backend: str
    local_endpoint: str


@dataclass(frozen=True)
class Config:
    companies: list[CompanyConfig] = field(default_factory=list)
    filing_types: list[str] = field(default_factory=list)
    date_range: dict = field(default_factory=dict)
    edgar: EdgarConfig = field(
        default_factory=lambda: EdgarConfig("", "", "", "", 8.0)
    )
    paths: PathsConfig = field(default_factory=lambda: PathsConfig("", "", "", ""))
    models: ModelsConfig = field(default_factory=lambda: ModelsConfig("", "", "", ""))
    opensearch: OpenSearchConfig = field(default_factory=lambda: OpenSearchConfig("", "local", ""))

    def company(self, ticker: str) -> CompanyConfig:
        for company in self.companies:
            if company.ticker == ticker:
                return company
        raise KeyError(f"no company with ticker {ticker!r}; known: {[c.ticker for c in self.companies]}")


def load_config(path: Path | str = "config/config.yaml") -> Config:
    raw = yaml.safe_load(Path(path).read_text())
    return Config(
        companies=[CompanyConfig(**entry) for entry in raw.get("companies", [])],
        filing_types=raw.get("filing_types", []),
        date_range=raw.get("date_range", {}),
        edgar=EdgarConfig(**raw["edgar"]),
        paths=PathsConfig(**raw["paths"]),
        models=ModelsConfig(**raw["models"]),
        opensearch=OpenSearchConfig(**raw["opensearch"]),
    )
