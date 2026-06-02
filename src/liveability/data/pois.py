"""OSM POI counts per suburb via the Overpass API — resilient.

Tries several public Overpass mirrors; returns ``None`` if all are unreachable (the
caller then falls back to modelled dimensions). When reachable it returns real,
per-suburb counts of parks / schools / hospitals via a point-in-polygon spatial join.
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
CATEGORIES = {
    "park": '(node["leisure"="park"];way["leisure"="park"];)',
    "school": '(node["amenity"="school"];way["amenity"="school"];)',
    "hospital": '(node["amenity"~"hospital|clinic|doctors"];)',
}


def _overpass(filter_expr: str, bbox: tuple[float, float, float, float], timeout: int) -> list | None:
    import requests

    south, west, north, east = bbox
    query = f"[out:json][timeout:{timeout}];{filter_expr}({south},{west},{north},{east});out center;"
    for url in MIRRORS:
        try:
            resp = requests.post(url, data=query, timeout=timeout)
            ctype = resp.headers.get("content-type", "")
            if resp.ok and ctype.startswith("application/json"):
                return resp.json().get("elements", [])
        except Exception as exc:  # noqa: BLE001
            logger.warning("overpass mirror failed (%s): %s", url, exc)
    return None


def fetch_pois(gdf, config=None, timeout: int = 40) -> pd.DataFrame | None:
    """Per-suburb POI counts, or None if Overpass is unreachable."""
    import geopandas as gpd
    from shapely.geometry import Point

    minx, miny, maxx, maxy = gdf.total_bounds
    bbox = (miny, minx, maxy, maxx)
    counts = pd.DataFrame(0, index=gdf.index, columns=list(CATEGORIES))

    for cat, filt in CATEGORIES.items():
        elements = _overpass(filt, bbox, timeout)
        if not elements:
            logger.warning("no Overpass data for %s — falling back to modelled dimensions", cat)
            return None
        pts = []
        for el in elements:
            lon = el.get("lon") or el.get("center", {}).get("lon")
            lat = el.get("lat") or el.get("center", {}).get("lat")
            if lon is not None and lat is not None:
                pts.append(Point(lon, lat))
        if not pts:
            continue
        pgdf = gpd.GeoDataFrame(geometry=pts, crs=4326)
        joined = gpd.sjoin(pgdf, gdf[["geometry"]], predicate="within")
        vc = joined["index_right"].value_counts()
        counts[cat] = counts.index.map(vc).fillna(0).astype(int)

    logger.info("fetched OSM POIs: %s", {c: int(counts[c].sum()) for c in CATEGORIES})
    return counts
