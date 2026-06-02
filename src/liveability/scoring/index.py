"""Composite liveability index.

Each dimension is scaled to 0–100, then combined into a single score. Default
weights come from the first principal component (PCA) — i.e. the data decides the
weighting — but the dashboard lets a user override them for a personalised score.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler


def normalize_dimensions(df: pd.DataFrame, dimensions: list[str]) -> pd.DataFrame:
    """Scale each dimension to 0–100 (min–max)."""
    out = df.copy()
    out[dimensions] = MinMaxScaler((0, 100)).fit_transform(df[dimensions].to_numpy())
    return out


def pca_weights(df: pd.DataFrame, dimensions: list[str], random_state: int = 42) -> tuple[dict[str, float], float]:
    """Return (normalised PC1 weights, explained-variance-ratio)."""
    x = df[dimensions].to_numpy()
    xs = (x - x.mean(axis=0)) / (x.std(axis=0) + 1e-9)
    pca = PCA(n_components=1, random_state=random_state).fit(xs)
    weights = np.abs(pca.components_[0])
    weights = weights / weights.sum()
    return dict(zip(dimensions, weights.tolist(), strict=False)), float(pca.explained_variance_ratio_[0])


def composite_score(df: pd.DataFrame, dimensions: list[str], weights: dict[str, float] | None = None) -> np.ndarray:
    """Weighted average of the (0–100) dimensions → a 0–100 liveability score."""
    if weights is None:
        weights = {d: 1.0 / len(dimensions) for d in dimensions}
    total = sum(weights.get(d, 0.0) for d in dimensions) or 1.0
    w = np.array([weights.get(d, 0.0) / total for d in dimensions])
    return np.clip(df[dimensions].to_numpy() @ w, 0, 100)
