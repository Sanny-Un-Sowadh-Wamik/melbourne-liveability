"""Real Melbourne suburb boundaries from a keyless GeoJSON.

Downloads Victorian suburb polygons once (cached), keeps those within ``max_cbd_km``
of the CBD (≈ Greater Melbourne), and derives geometry features (area, centroid,
distance to CBD) — all real, no external API required.
"""

from __future__ import annotations

import logging

import numpy as np

from liveability.config import AppConfig, load_config

logger = logging.getLogger(__name__)

RAW_NAME = "vic_suburbs.geojson"
# Property that holds the suburb name varies by source — try these in order.
NAME_KEYS = ["name", "Name", "NAME", "suburb", "Suburb", "SUBURB", "vic_loca_2", "VIC_LOCA_2", "loc_name", "SSC_NAME"]
VICGRID = 3111  # GDA94 / Vicgrid94 — metres, accurate for Victoria


def _haversine_km(lat: np.ndarray, lon: np.ndarray, lat0: float, lon0: float) -> np.ndarray:
    r = 6371.0
    dlat, dlon = np.radians(lat - lat0), np.radians(lon - lon0)
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat0)) * np.cos(np.radians(lat)) * np.sin(dlon / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def load_boundaries(config: AppConfig | None = None, force: bool = False):
    """Return a GeoDataFrame of Greater-Melbourne suburbs with geometry features."""
    import geopandas as gpd

    config = config or load_config()
    cache = config.data.raw_dir / RAW_NAME

    if force or not cache.exists():
        import requests

        config.data.raw_dir.mkdir(parents=True, exist_ok=True)
        logger.info("downloading boundaries: %s", config.data.boundaries_url)
        resp = requests.get(config.data.boundaries_url, timeout=90)
        resp.raise_for_status()
        cache.write_bytes(resp.content)
    gdf = gpd.read_file(cache)

    name_col = next((k for k in NAME_KEYS if k in gdf.columns), None)
    if name_col is None:
        name_col = next(c for c in gdf.columns if c != "geometry")
    gdf = gdf.rename(columns={name_col: "suburb"})[["suburb", "geometry"]]
    gdf["suburb"] = gdf["suburb"].astype(str).str.title()

    if gdf.crs is None:
        gdf = gdf.set_crs(4326)
    gdf = gdf.to_crs(4326)

    proj = gdf.to_crs(VICGRID)
    gdf["area_km2"] = (proj.area / 1e6).round(3)
    cent = proj.geometry.centroid.to_crs(4326)
    gdf["lat"], gdf["lon"] = cent.y.round(5), cent.x.round(5)
    gdf["cbd_km"] = _haversine_km(
        gdf["lat"].to_numpy(), gdf["lon"].to_numpy(), config.data.cbd_lat, config.data.cbd_lon
    ).round(2)

    melb = gdf[(gdf["cbd_km"] <= config.data.max_cbd_km) & (gdf["area_km2"] > 0)].copy()
    melb = melb.dissolve(by="suburb", aggfunc="first").reset_index()  # merge multi-part suburbs
    logger.info("loaded %d VIC suburbs → %d within %.0f km of CBD", len(gdf), len(melb), config.data.max_cbd_km)
    return melb.reset_index(drop=True)
