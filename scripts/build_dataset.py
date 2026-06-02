"""Build the scored liveability dataset.

boundaries → (OSM POIs if reachable) → 8 dimensions → 0–100 normalise → PCA-weighted
composite → ranked GeoJSON + metadata, committed for the demo.

Run:  python scripts/build_dataset.py
"""

from __future__ import annotations

import json
import logging

from liveability.config import load_config
from liveability.data import fetch_pois, load_boundaries
from liveability.features import build_dimensions
from liveability.scoring import composite_score, normalize_dimensions, pca_weights

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("build")


def main() -> None:
    cfg = load_config()
    gdf = load_boundaries(cfg)

    try:
        pois = fetch_pois(gdf, cfg)
    except Exception as exc:  # noqa: BLE001
        log.warning("POI fetch errored: %s", exc)
        pois = None

    dims, modelled = build_dimensions(gdf, pois)
    for col in cfg.scoring.dimensions:
        gdf[col] = dims[col].to_numpy()

    gdf = normalize_dimensions(gdf, cfg.scoring.dimensions)
    weights, evr = pca_weights(gdf, cfg.scoring.dimensions, cfg.data.random_state)
    gdf["liveability"] = composite_score(gdf, cfg.scoring.dimensions, weights).round(1)
    gdf = gdf.sort_values("liveability", ascending=False).reset_index(drop=True)
    gdf["rank"] = range(1, len(gdf) + 1)

    cfg.data.sample_dir.mkdir(parents=True, exist_ok=True)
    out = cfg.data.sample_dir / "melbourne_liveability.geojson"
    gdf.to_file(out, driver="GeoJSON")
    meta = {
        "n_suburbs": int(len(gdf)),
        "dimensions": cfg.scoring.dimensions,
        "pca_explained_variance": round(evr, 3),
        "pca_weights": {k: round(v, 3) for k, v in weights.items()},
        "osm_pois_available": pois is not None,
        "modelled_dimensions": modelled,
        "real_dimensions": [d for d in cfg.scoring.dimensions if d not in modelled],
        "cbd": [cfg.data.cbd_lat, cfg.data.cbd_lon],
    }
    (cfg.data.sample_dir / "metadata.json").write_text(json.dumps(meta, indent=2))
    log.info("saved %d suburbs → %s (PCA explained variance=%.2f)", len(gdf), out, evr)

    print("\nPCA weights:", {k: round(v, 2) for k, v in weights.items()})
    print(f"OSM POIs available: {pois is not None} | modelled dims: {modelled}\n")
    print("Top 10 suburbs by liveability:")
    print(gdf[["rank", "suburb", "liveability", "cbd_km", "transport", "walkability"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
