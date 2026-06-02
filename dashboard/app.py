"""Streamlit dashboard — interactive Melbourne liveability map.

Self-contained: reads the committed scored GeoJSON, lets the user re-weight the
dimensions live, and recolours a Folium choropleth. Honest about which dimensions
are real vs modelled.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import geopandas as gpd
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from liveability.config import REPO_ROOT
from liveability.scoring import composite_score
from liveability.viz import make_map

st.set_page_config(page_title="Melbourne Liveability", page_icon="🗺️", layout="wide")

SAMPLE = REPO_ROOT / "data" / "sample"


@st.cache_data(show_spinner=False)
def load_data():
    gdf = gpd.read_file(SAMPLE / "melbourne_liveability.geojson")
    meta = json.loads((SAMPLE / "metadata.json").read_text())
    return gdf, meta


try:
    gdf, META = load_data()
except Exception:
    st.error("Scored dataset not found — run `python scripts/build_dataset.py`, then reload.")
    st.stop()

dims = META["dimensions"]
modelled = set(META["modelled_dimensions"])
pca_w = META["pca_weights"]

st.title("🗺️ Melbourne Suburb Liveability")
st.caption(
    f"Real geometry for **{META['n_suburbs']} Greater-Melbourne suburbs** + a PCA-weighted composite index "
    "across 8 dimensions. Drag the weights to build *your* liveability score."
)
st.warning(
    "**Methodology prototype.** Suburb *geometry* is real; **transport, walkability & affordability** are derived "
    "from real geometry, but **green space, education, health, safety & demographics** are currently *modelled* "
    "(the live OSM/ABS feeds were unreachable at build time). Re-run `build_dataset.py` on an open network to "
    "populate real OSM data. Not for real decisions.",
    icon="⚠️",
)

with st.sidebar:
    st.header("Your weights")
    st.caption("Defaults = PCA (the data's own weighting). ✅ = real signal, ~ = modelled.")
    weights = {}
    for d in dims:
        label = f"{'✅' if d not in modelled else '〜'} {d}"
        weights[d] = st.slider(label, 0.0, 1.0, float(pca_w.get(d, 0.125)), 0.01)
    st.markdown("---")
    st.metric("PCA explained variance", f"{META['pca_explained_variance'] * 100:.0f}%")

gdf = gdf.copy()
gdf["liveability"] = composite_score(gdf, dims, weights).round(1)
gdf = gdf.sort_values("liveability", ascending=False).reset_index(drop=True)
gdf["rank"] = range(1, len(gdf) + 1)

map_col, table_col = st.columns([2, 1])
with map_col:
    st_folium(make_map(gdf), height=540, width=820, returned_objects=[])
with table_col:
    st.subheader("🏆 Top 10")
    st.dataframe(gdf[["rank", "suburb", "liveability"]].head(10), hide_index=True, width="stretch")
    st.subheader("🔻 Bottom 5")
    st.dataframe(gdf[["rank", "suburb", "liveability"]].tail(5), hide_index=True, width="stretch")

with st.expander("ℹ️ Dimensions: real vs modelled"):
    rows = [
        {
            "dimension": d,
            "source": "real (geometry/OSM)" if d not in modelled else "modelled placeholder",
            "PCA weight": round(pca_w.get(d, 0), 3),
        }
        for d in dims
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
