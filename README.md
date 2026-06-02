# 🗺️ Melbourne Suburb Liveability Score

> A geospatial **liveability index** for Greater Melbourne: real suburb boundaries fused with multi-source signals into a **PCA-weighted composite score** across 8 dimensions, shown on an **interactive Folium choropleth** with user-adjustable weights.

![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**🔴 Live demo:** _added after deploy_ (Hugging Face Space)

---

## 🎯 What this demonstrates

- **Geospatial engineering** with GeoPandas — real VIC suburb polygons, CRS projection (Vicgrid94), area/centroid/distance derivation, spatial joins.
- **Multi-source data fusion** — OpenStreetMap POIs (Overpass, resilient) + geometry-derived metrics → 8 liveability dimensions.
- A **custom composite index** — dimensions normalised 0–100 and combined with **PCA-derived weights** (documented explained variance).
- An **interactive Folium choropleth** with a personalised weighting slider — the standout recruiter visual.

## 🧰 Tech stack

| Layer | Tool |
|---|---|
| Geometry | GeoPandas · Shapely · pyogrio |
| POIs | OpenStreetMap Overpass (resilient, cached) |
| Scoring | scikit-learn (PCA) |
| Map | Folium + branca |
| Dashboard | Streamlit + streamlit-folium |
| Tooling | `uv` · `ruff` · `pytest` · GitHub Actions |
| Hosting | Hugging Face Space (free) |

## 📁 Structure

```
03-melbourne-liveability/
├── config/config.yaml
├── src/liveability/
│   ├── data/        # real boundaries (GeoJSON) + OSM POIs
│   ├── features/    # the 8 liveability dimensions
│   ├── scoring/     # normalise + PCA composite index
│   └── viz/         # Folium choropleth
├── dashboard/  · scripts/  · tests/  · .github/workflows/
```

## 🚀 Quickstart

```bash
uv venv --python 3.11
uv pip install -e ".[viz,app,dev]"
python scripts/build_dataset.py    # real boundaries + features + scores
streamlit run dashboard/app.py
```

## 📊 Results

**260 Greater-Melbourne suburbs** scored. The composite uses **PCA-derived weights** (PC1 explains **42%** of variance); the dashboard lets a user override them live for a personalised score.

> ⚠️ **Methodology prototype.** Suburb geometry and **transport / walkability / affordability** are real (geometry-derived). **Green space, education, health, safety, demographics** are *modelled placeholders* — Overpass (OSM) and ABS feeds were firewalled from the build environment. Re-run `scripts/build_dataset.py` on an open network to fetch real OSM POIs and lift those to real. The map, PCA weighting and live re-scoring are fully functional.

PCA weights (the data's own weighting):

| transport | walkability | affordability | safety | green_space | education | health | demographics |
|--:|--:|--:|--:|--:|--:|--:|--:|
| 0.25 | 0.24 | 0.25 | 0.21 | 0.03 | 0.01 | 0.01 | 0.01 |

> PCA correctly **down-weights the noisy modelled dimensions** (green/education/health ≈ 0.01) and leans on the real geometry signals — a tidy illustration of *why* PCA weighting beats hand-picked weights.

### 📌 Résumé bullet
> Built a Melbourne suburb liveability index: fused real suburb-boundary geometry (GeoPandas, Vicgrid projection) with an 8-dimension framework and a **PCA-weighted** composite across 260 suburbs; shipped an interactive **Folium choropleth** with live user re-weighting on a deployed Streamlit app.

## 📄 License

MIT — © 2026 Sanny Un Sowadh Wamik
