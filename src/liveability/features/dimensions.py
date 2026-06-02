"""The eight liveability dimensions.

Honesty model:
  * **transport, walkability, affordability** — derived from *real geometry*
    (distance to CBD ≈ public-transport access; suburb density ≈ walkability; the
    centrality gradient ≈ relative un-affordability).
  * **green_space, education, health** — real OSM POI densities when the Overpass
    API is reachable, otherwise a deterministic (suburb-seeded) model.
  * **safety, demographics** — need survey/census data (no live source here), so they
    are deterministically modelled.

Every modelled dimension is reported in ``modeled`` so the README/dashboard stay honest.
All modelled values are seeded by suburb name → fully reproducible.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

OSM_BACKED = {"green_space": "park", "education": "school", "health": "hospital"}
ALWAYS_MODELLED = ["safety", "demographics"]


def _unit(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    lo, hi = np.nanmin(x), np.nanmax(x)
    return (x - lo) / (hi - lo + 1e-9)


def _seed(names: list[str], salt: str) -> np.ndarray:
    return np.array([int(hashlib.md5(f"{salt}:{n}".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF for n in names])


def build_dimensions(gdf, pois: pd.DataFrame | None = None) -> tuple[pd.DataFrame, list[str]]:
    """Return (dimensions DataFrame [0–100], list of modelled dimension names)."""
    cbd = gdf["cbd_km"].to_numpy()
    area = gdf["area_km2"].to_numpy()
    names = gdf["suburb"].tolist()
    density = 1.0 / np.clip(area, 0.1, None)

    d = pd.DataFrame(index=gdf.index)
    modelled: list[str] = []

    # ── real, geometry-derived ───────────────────────────────────────────────
    d["transport"] = 100 * np.exp(-cbd / 8.0)
    d["walkability"] = 100 * (0.6 * _unit(density) + 0.4 * np.exp(-cbd / 10.0))
    d["affordability"] = 100 * (0.25 + 0.75 * _unit(cbd))  # cheaper further from CBD

    # ── OSM-backed, else modelled ────────────────────────────────────────────
    for dim, key in OSM_BACKED.items():
        if pois is not None and key in pois.columns:
            d[dim] = 100 * _unit(pois[key].to_numpy())
        else:
            d[dim] = 100 * (0.2 + 0.6 * _seed(names, dim))
            modelled.append(dim)

    # ── modelled (no live survey source) ─────────────────────────────────────
    d["safety"] = 100 * np.clip(0.45 + 0.3 * _unit(cbd) + 0.25 * (_seed(names, "safety") - 0.5), 0, 1)
    d["demographics"] = 100 * (0.3 + 0.5 * _seed(names, "demographics"))
    modelled += ALWAYS_MODELLED

    return d.round(1), modelled
