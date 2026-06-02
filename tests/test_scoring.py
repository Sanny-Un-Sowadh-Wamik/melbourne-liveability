"""Scoring tests (hermetic)."""

import pandas as pd

from liveability.scoring import composite_score, normalize_dimensions, pca_weights

DIMS = ["a", "b", "c"]


def _df() -> pd.DataFrame:
    return pd.DataFrame({"a": [0.0, 5.0, 10.0], "b": [10.0, 5.0, 0.0], "c": [1.0, 2.0, 3.0]})


def test_normalize_to_0_100():
    out = normalize_dimensions(_df(), DIMS)
    for col in DIMS:
        assert out[col].min() == 0.0
        assert out[col].max() == 100.0


def test_pca_weights_sum_to_one():
    weights, evr = pca_weights(_df(), DIMS)
    assert abs(sum(weights.values()) - 1.0) < 1e-6
    assert 0.0 <= evr <= 1.0


def test_composite_in_range_and_weighting():
    df = normalize_dimensions(_df(), DIMS)
    score = composite_score(df, DIMS, {"a": 1.0, "b": 1.0, "c": 1.0})
    assert (score >= 0).all() and (score <= 100).all()
    # all-weight-on-a should equal a's normalised column
    only_a = composite_score(df, DIMS, {"a": 1.0, "b": 0.0, "c": 0.0})
    assert abs(only_a[-1] - 100.0) < 1e-6
