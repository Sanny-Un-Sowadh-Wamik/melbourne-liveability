"""Dimension-building tests (hermetic)."""

import numpy as np
import pandas as pd

from liveability.features import build_dimensions

EIGHT = ["transport", "walkability", "green_space", "safety", "affordability", "education", "health", "demographics"]


def _g(n: int = 20) -> pd.DataFrame:
    return pd.DataFrame(
        {"suburb": [f"S{i}" for i in range(n)], "cbd_km": np.linspace(1, 25, n), "area_km2": np.linspace(0.5, 10, n)}
    )


def test_all_dimensions_in_range():
    dims, modelled = build_dimensions(_g())
    for col in EIGHT:
        assert (dims[col] >= 0).all() and (dims[col] <= 100).all()
    # geometry-derived dimensions are NOT flagged modelled
    assert "transport" not in modelled and "walkability" not in modelled and "affordability" not in modelled
    assert "safety" in modelled and "demographics" in modelled


def test_deterministic():
    a, _ = build_dimensions(_g())
    b, _ = build_dimensions(_g())
    pd.testing.assert_frame_equal(a, b)


def test_transport_decays_with_distance():
    dims, _ = build_dimensions(_g())
    # closer to CBD (row 0) → higher transport than far (last row)
    assert dims["transport"].iloc[0] > dims["transport"].iloc[-1]
