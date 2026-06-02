"""Geometry-helper tests (hermetic — no network)."""

import numpy as np

from liveability.data.boundaries import _haversine_km


def test_haversine_zero_distance():
    d = _haversine_km(np.array([-37.81]), np.array([144.96]), -37.81, 144.96)[0]
    assert d < 0.05


def test_haversine_known_distance():
    # ~0.04° longitude at Melbourne's latitude ≈ 3.5 km
    d = _haversine_km(np.array([-37.81]), np.array([145.00]), -37.81, 144.96)[0]
    assert 3.0 < d < 4.5
