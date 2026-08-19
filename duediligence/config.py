"""
Typed config loading from config/config.yaml.

One loader, one place that knows the file's shape — everything else in the
project imports a `Config` instance rather than parsing YAML itself.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

__all__ = [
    "CompanyConfig", "Config", "EdgarConfig", "ModelsConfig",
    "OpenSearchConfig", "PathsConfig", "PROFILE_ENV_VAR", "load_config",
]

#: Selects a profile without a code change or a rebuilt image, following the
#: precedent already set by the two OpenSearch overrides below.
PROFILE_ENV_VAR = "DUEDILIGENCE_CONFIG_PROFILE"


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
    #: The profile actually applied, or None for the base configuration.
    #: Recorded at load time so a running process can report which profile
    #: it is on without re-reading an environment variable that may have
    #: changed since startup — the env var says what was asked for, this
    #: says what was built.
    profile: str | None = None

    def company(self, ticker: str) -> CompanyConfig:
        for company in self.companies:
            if company.ticker == ticker:
                return company
        raise KeyError(f"no company with ticker {ticker!r}; known: {[c.ticker for c in self.companies]}")


def _deep_merge(base: dict, overlay: dict) -> dict:
    """Overlay wins, key by key, recursing into nested mappings.

    Recursive rather than top-level so a profile can set one model without
    also having to restate the other three — a profile that had to repeat
    every sibling key would drift from the base the moment the base changed,
    which is the failure mode profiles exist to avoid.
    """
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _apply_profile(raw: dict, profile: str, config_path: Path) -> dict:
    """Merge a named profile over the base config, or explain why it cannot.

    Profiles are selected by name and resolved inside a tracked directory
    rather than taken as a path. A path would let an experiment run against
    an untracked overlay sitting outside the repository, which makes the
    resulting report unreproducible by anyone else.
    """
    profiles_dir = config_path.parent / "profiles"
    profile_path = profiles_dir / f"{profile}.yaml"
    if not profile_path.is_file():
        available = sorted(p.stem for p in profiles_dir.glob("*.yaml"))
        raise ValueError(
            f"unknown config profile {profile!r} (looked for {profile_path}); "
            f"available profiles: {available or 'none'}. Refusing to fall back "
            "to the base configuration — a silent fallback produces a report "
            "labelled with the profile that actually measured the baseline."
        )

    overlay = yaml.safe_load(profile_path.read_text()) or {}
    merged = _deep_merge(raw, overlay)

    # An index holds vectors from exactly one embedding model. Pointing a
    # second model at the same index scores cosine similarity across two
    # incompatible spaces — no error, no warning, and no recovery short of
    # re-embedding all 38,483 chunks. The one direction that is safe is a new
    # index under the same model, so only the model-changed case is checked.
    if merged["models"]["embedding_model"] != raw["models"]["embedding_model"]:
        if merged["opensearch"]["index_name"] == raw["opensearch"]["index_name"]:
            raise ValueError(
                f"profile {profile!r} changes models.embedding_model to "
                f"{merged['models']['embedding_model']!r} but leaves "
                f"opensearch.index_name as {raw['opensearch']['index_name']!r}. "
                "A profile must change both together: one index holds one "
                "model's vectors, and mixing two produces silently meaningless "
                "similarity scores rather than an error."
            )
    return merged


def load_config(
    path: Path | str = "config/config.yaml", *, profile: str | None = None
) -> Config:
    """Load config from YAML, with environment overrides for deployment.

    The YAML holds the developer default (``http://localhost:9200``), which
    is wrong in every deployed context: inside a Docker network OpenSearch
    is reachable by service name, and in Kubernetes by service DNS —
    ``localhost`` in a container is the container itself. Rather than ship
    a second config file per environment, the two values that actually
    change between environments are overridable by env var:

        DUEDILIGENCE_OPENSEARCH_ENDPOINT   e.g. http://opensearch:9200
        DUEDILIGENCE_OPENSEARCH_BACKEND    "local" | "aws"

    A ``profile`` names a tracked YAML overlay in ``config/profiles/`` and is
    merged over the base before those overrides apply. It returns the same
    ``Config`` every caller already receives, so no consumer's signature
    changes and no consumer has to learn that profiles exist. Selection is
    also available as ``DUEDILIGENCE_CONFIG_PROFILE``, with this argument
    taking precedence.
    """
    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text())

    selected = profile if profile is not None else os.environ.get(PROFILE_ENV_VAR) or None
    if selected:
        raw = _apply_profile(raw, selected, config_path)

    opensearch = dict(raw["opensearch"])
    if endpoint := os.environ.get("DUEDILIGENCE_OPENSEARCH_ENDPOINT"):
        opensearch["local_endpoint"] = endpoint
    if backend := os.environ.get("DUEDILIGENCE_OPENSEARCH_BACKEND"):
        opensearch["backend"] = backend
    raw["opensearch"] = opensearch

    return Config(
        companies=[CompanyConfig(**entry) for entry in raw.get("companies", [])],
        filing_types=raw.get("filing_types", []),
        date_range=raw.get("date_range", {}),
        edgar=EdgarConfig(**raw["edgar"]),
        paths=PathsConfig(**raw["paths"]),
        models=ModelsConfig(**raw["models"]),
        opensearch=OpenSearchConfig(**raw["opensearch"]),
        profile=selected,
    )
