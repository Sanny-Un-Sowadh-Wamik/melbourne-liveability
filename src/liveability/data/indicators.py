"""Real City of Melbourne liveability & social indicators (time series).

Source: City of Melbourne open data — 319 indicators across 15 topics, many with
multi-year series. City-level (not per-suburb), so used for a *real* indicators
explorer alongside the (prototype) per-suburb map.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from liveability.config import REPO_ROOT

RAW_CSV = REPO_ROOT / "data" / "raw" / "city-of-melbourne-liveability-and-social-indicators (1).csv"
SAMPLE = REPO_ROOT / "data" / "sample" / "melbourne_indicators.parquet"
KEEP = ["Type", "Topic", "Indicator", "Period", "year", "Value", "Value_Type", "Sources"]


def _to_year(period: str) -> int | None:
    m = re.search(r"(19|20)\d{2}", str(period))
    return int(m.group()) if m else None


def build_indicators_sample(csv: Path | None = None) -> pd.DataFrame:
    """Clean the raw CSV into a committed Parquet (numeric Value + parsed year)."""
    df = pd.read_csv(csv or RAW_CSV)
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df["year"] = df["Period"].map(_to_year)
    df["Sources"] = df["Sources"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    out = df.dropna(subset=["Value", "year"])[KEEP].reset_index(drop=True)
    SAMPLE.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(SAMPLE)
    return out


def load_indicators() -> pd.DataFrame:
    """Load the committed indicators (build from raw CSV on a cold start if needed)."""
    if SAMPLE.exists():
        return pd.read_parquet(SAMPLE)
    return build_indicators_sample()
