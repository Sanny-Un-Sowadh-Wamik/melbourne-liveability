"""Folium choropleth of suburb scores."""

from __future__ import annotations


def make_map(gdf, value_col: str = "liveability", center=(-37.8136, 144.9631), zoom: int = 10):
    import branca.colormap as cm
    import folium

    vmin, vmax = float(gdf[value_col].min()), float(gdf[value_col].max())
    colormap = cm.LinearColormap(
        ["#d73027", "#fee08b", "#1a9850"], vmin=vmin, vmax=vmax, caption=f"{value_col} score (0–100)"
    )
    fmap = folium.Map(location=center, zoom_start=zoom, tiles="cartodbpositron")
    folium.GeoJson(
        gdf.to_json(),
        style_function=lambda feat: {
            "fillColor": colormap(feat["properties"][value_col]),
            "color": "white",
            "weight": 0.4,
            "fillOpacity": 0.75,
        },
        highlight_function=lambda _feat: {"weight": 2, "color": "#333"},
        tooltip=folium.GeoJsonTooltip(
            fields=["suburb", value_col, "rank"],
            aliases=["Suburb", "Score", "Rank"],
            localize=True,
        ),
    ).add_to(fmap)
    colormap.add_to(fmap)
    return fmap
