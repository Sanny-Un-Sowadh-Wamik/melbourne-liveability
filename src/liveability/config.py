"""Typed configuration for the liveability pipeline."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[1]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "config.yaml"


class DataConfig(BaseModel):
    boundaries_url: str
    cbd_lat: float = -37.8136
    cbd_lon: float = 144.9631
    max_cbd_km: float = 25.0
    random_state: int = 42
    raw_dir: Path = REPO_ROOT / "data" / "raw"
    processed_dir: Path = REPO_ROOT / "data" / "processed"
    sample_dir: Path = REPO_ROOT / "data" / "sample"


class ScoringConfig(BaseModel):
    dimensions: list[str]
    pca_components: int = 1


class AppConfig(BaseModel):
    project_name: str = "melbourne-liveability"
    data: DataConfig
    scoring: ScoringConfig


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    overpass_url: str | None = None


@lru_cache
def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    with open(path) as fh:
        raw = yaml.safe_load(fh)
    return AppConfig(**raw)


@lru_cache
def get_settings() -> Settings:
    return Settings()
