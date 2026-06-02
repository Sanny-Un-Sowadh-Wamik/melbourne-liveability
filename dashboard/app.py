"""Premium interactive Melbourne liveability dashboard.

Reads the committed scored GeoJSON + real City-of-Melbourne indicators. Three tabs:
an interactive choropleth (live re-weighting), a real-data indicators explorer, and
an honest methodology note.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parent / "src"
for _p in (_HERE, _SRC):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import geopandas as gpd
import pandas as pd
import plotly.express as px
import streamlit as st
import theme
from streamlit_folium import st_folium

from liveability.config import REPO_ROOT
from liveability.data.indicators import load_indicators
from liveability.scoring import composite_score
from liveability.viz import make_map

st.set_page_config(page_title="Melbourne Liveability", page_icon="🗺️", layout="wide")
theme.inject()

SAMPLE = REPO_ROOT / "data" / "sample"


@st.cache_data(show_spinner=False)
def load_geo():
    gdf = gpd.read_file(SAMPLE / "melbourne_liveability.geojson")
    meta = json.loads((SAMPLE / "metadata.json").read_text())
    return gdf, meta


@st.cache_data(show_spinner=False)
def load_ind():
    return load_indicators()


try:
    GDF, META = load_geo()
except Exception:
    st.error("Scored dataset not found — run `python scripts/build_dataset.py`, then reload.")
    st.stop()

dims = META["dimensions"]
modelled = set(META["modelled_dimensions"])
pca_w = META["pca_weights"]

theme.hero(
    "🗺️ Melbourne Suburb Liveability",
    f"Real geography for {META['n_suburbs']} Greater-Melbourne suburbs · a PCA-weighted index you can re-weight "
    "live · plus 100+ real City-of-Melbourne indicators.",
    tag="GEOSPATIAL · PCA · INTERACTIVE",
)

with st.expander("⚙️  Build your score  ·  dimension weights", expanded=True):
    hc1, hc2 = st.columns([3, 1])
    real_only = hc1.toggle(
        "Real signals only (coherent ranking)",
        value=True,
        help="Use only the geometry-derived dimensions (transport, walkability, affordability) for a coherent map. "
        "Turn off to include the modelled placeholders.",
    )
    hc2.metric("PCA var.", f"{META['pca_explained_variance'] * 100:.0f}%")
    st.caption("Weights default to PCA. ✅ real · 〜 modelled")
    wcols = st.columns(4)
    weights = {}
    for i, d in enumerate(dims):
        is_mod = d in modelled
        disabled = real_only and is_mod
        default = 0.0 if disabled else float(pca_w.get(d, 0.125))
        weights[d] = wcols[i % 4].slider(f"{'〜' if is_mod else '✅'} {d}", 0.0, 1.0, default, 0.01, disabled=disabled)

g = GDF.copy()
g["liveability"] = composite_score(g, dims, weights).round(1)
g = g.sort_values("liveability", ascending=False).reset_index(drop=True)
g["rank"] = range(1, len(g) + 1)

tab_map, tab_ind, tab_method = st.tabs(["🗺️  Liveability map", "📊  Real indicators", "ℹ️  Methodology"])

with tab_map:
    c1, c2, c3 = st.columns(3)
    c1.metric("Suburbs scored", META["n_suburbs"])
    c2.metric("🏆 Top suburb", g["suburb"].iloc[0], f"{g['liveability'].iloc[0]:.0f}/100")
    c3.metric("Mode", "Real signals" if real_only else "All 8 dims")
    map_col, table_col = st.columns([2, 1])
    with map_col:
        st_folium(make_map(g), height=540, width=860, returned_objects=[])
    with table_col:
        st.markdown("#### 🏆 Top 10")
        st.dataframe(g[["rank", "suburb", "liveability"]].head(10), hide_index=True, width="stretch", height=250)
        st.markdown("#### 🔻 Bottom 5")
        st.dataframe(g[["rank", "suburb", "liveability"]].tail(5), hide_index=True, width="stretch", height=140)

with tab_ind:
    ind = load_ind()
    st.markdown("#### 📊 Real City-of-Melbourne liveability & social indicators")
    st.caption("City of Melbourne open data · 103 indicators · 15 topics · 2006–2020 · **real data, not modelled**.")
    cc1, cc2 = st.columns(2)
    topic = cc1.selectbox("Topic", sorted(ind["Topic"].unique()))
    sub = ind[ind["Topic"] == topic]
    indicator = cc2.selectbox("Indicator", sorted(sub["Indicator"].unique()))
    series = sub[sub["Indicator"] == indicator].sort_values("year")
    latest = series.iloc[-1]
    unit = {"Percentage": " %", "Dollars": " $"}.get(latest["Value_Type"], "")
    k1, k2, k3 = st.columns(3)
    k1.metric("Latest value", f"{latest['Value']:,.1f}{unit}")
    k2.metric("Period", str(latest["Period"]))
    k3.metric("Data points", len(series))
    if len(series) > 1:
        fig = px.area(series, x="year", y="Value", markers=True)
        fig.update_traces(line_color="#0f9d58", fillcolor="rgba(15,157,88,.12)")
        fig.update_layout(title=indicator[:95], height=360, **theme.PLOTLY_LAYOUT)
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Single data point — no trend to plot.")
    st.caption("🔗 Source: " + str(latest["Sources"])[:280])

with tab_method:
    st.markdown("#### How the suburb index is built")
    st.markdown(
        "- **Real:** 260 suburb boundaries (GeoPandas, Vicgrid projection); **transport, walkability, affordability** "
        "derived from geometry (CBD distance + density).\n"
        "- **Modelled placeholders:** green space, education, health, safety, demographics — the live OSM (Overpass) "
        "and ABS feeds were firewalled from the build environment. `scripts/build_dataset.py` on an open network "
        "fetches real OSM POIs and lifts these to real.\n"
        "- The default **'Real signals only'** mode uses just the real dimensions, so the ranking stays coherent."
    )
    rows = [
        {
            "dimension": d,
            "source": "✅ real (geometry)" if d not in modelled else "〜 modelled placeholder",
            "PCA weight": round(pca_w.get(d, 0), 3),
        }
        for d in dims
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption("The **Real indicators** tab above is 100% real City-of-Melbourne open data.")
