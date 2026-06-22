"""Build the interactive folium map with all layers and the risk score choropleth."""

import folium
from folium.plugins import MiniMap, MeasureControl
import geopandas as gpd
import pandas as pd
import json


# Risk label → color for choropleth
RISK_COLORS = {
    "Low":       "#2ecc71",
    "Moderate":  "#f39c12",
    "High":      "#e74c3c",
    "Very High": "#8e1a0e",
}

# Layer colors
LAYER_STYLES = {
    "ugb":        {"color": "#2c3e50", "weight": 2, "fillOpacity": 0},
    "city":       {"color": "#2980b9", "weight": 2, "fillOpacity": 0.05, "fillColor": "#2980b9"},
    "fire_perim": {"color": "#e74c3c", "weight": 1, "fillOpacity": 0.2, "fillColor": "#e67e22"},
    "wui_high":   {"color": "#e74c3c", "weight": 0.5, "fillOpacity": 0.3, "fillColor": "#e74c3c"},
    "wui_med":    {"color": "#f39c12", "weight": 0.5, "fillOpacity": 0.3, "fillColor": "#f39c12"},
    "wui_low":    {"color": "#f1c40f", "weight": 0.5, "fillOpacity": 0.2, "fillColor": "#f1c40f"},
    "district":   {"color": "#8e44ad", "weight": 1.5, "fillOpacity": 0.05, "fillColor": "#8e44ad"},
}


def _gdf_to_geojson(gdf: gpd.GeoDataFrame) -> dict:
    return json.loads(gdf.to_json())


def _risk_style(feature):
    label = feature["properties"].get("risk_label", "Low")
    color = RISK_COLORS.get(str(label), "#95a5a6")
    return {
        "fillColor": color,
        "color": "#2c3e50",
        "weight": 2,
        "fillOpacity": 0.75,
    }


def _expansion_popup(feature) -> str:
    p = feature["properties"]
    label = p.get("risk_label", "N/A")
    color = RISK_COLORS.get(str(label), "#95a5a6")
    return f"""
    <div style="font-family: Arial; min-width: 220px;">
        <h4 style="margin:0 0 6px 0; color:#2c3e50">{p.get('NAME','Unknown')}</h4>
        <div style="background:{color}; color:white; padding:4px 8px; border-radius:4px;
                    display:inline-block; font-weight:bold; margin-bottom:8px;">
            {label} Risk — Score: {p.get('risk_score','N/A')}
        </div>
        <table style="width:100%; font-size:12px; border-collapse:collapse;">
            <tr><td><b>Acres</b></td><td>{round(p.get('ACRES',0),1)}</td></tr>
            <tr><td><b>Plan Type</b></td><td>{p.get('PLAN_TYPE','')}</td></tr>
            <tr><td><b>WUI Score</b></td><td>{p.get('wui_score','')}</td></tr>
            <tr><td><b>Fire Incidents Nearby</b></td><td>{p.get('fire_density','')}</td></tr>
            <tr><td><b>Dist. to Station</b></td><td>{round(p.get('dist_to_station_mi',0),1)} mi</td></tr>
            <tr><td><b>Burn Acres History</b></td><td>{round(p.get('burn_acres',0),1)}</td></tr>
            <tr><td><b>Inside City Limits</b></td><td>{'Yes' if p.get('in_city') else 'No'}</td></tr>
        </table>
    </div>
    """


def build_map(layers: dict, scored: gpd.GeoDataFrame, county: gpd.GeoDataFrame = None) -> folium.Map:
    # Center on Bend, OR
    m = folium.Map(
        location=[44.058, -121.315],
        zoom_start=11,
        tiles=None,
    )

    # Base tiles
    folium.TileLayer("CartoDB positron", name="Light Basemap", control=True).add_to(m)
    folium.TileLayer("CartoDB dark_matter", name="Dark Basemap", control=True).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Satellite",
        control=True,
    ).add_to(m)

    # --- Burn Probability tile overlay ---
    folium.TileLayer(
        tiles="https://tiles.arcgis.com/tiles/CD5mKowwN6nIaqd8/arcgis/rest/services/project_wre_bp_tile_package/MapServer/tile/{z}/{y}/{x}",
        attr="Oregon Explorer / USFS",
        name="Burn Probability",
        overlay=True,
        control=True,
        opacity=0.5,
        show=False,
    ).add_to(m)

    # --- County boundary (outline only, non-interactive so it never grabs hover) ---
    if county is not None and not county.empty:
        county_line = county.copy()
        county_line["geometry"] = county_line.geometry.boundary
        folium.GeoJson(
            _gdf_to_geojson(county_line),
            name="Deschutes County Limit",
            style_function=lambda x: {
                "color": "#f1c40f",
                "weight": 3,
                "dashArray": "8,6",
            },
        ).add_to(m)

    # --- UGB boundary ---
    if not layers["ugb_2022"].empty:
        folium.GeoJson(
            _gdf_to_geojson(layers["ugb_2022"]),
            name="Urban Growth Boundary",
            style_function=lambda x: LAYER_STYLES["ugb"],
            tooltip="Urban Growth Boundary",
        ).add_to(m)

    # --- City limits ---
    if not layers["city_limits"].empty:
        folium.GeoJson(
            _gdf_to_geojson(layers["city_limits"]),
            name="City Limits",
            style_function=lambda x: LAYER_STYLES["city"],
            tooltip=folium.GeoJsonTooltip(fields=["CITY"], aliases=["City:"]),
        ).add_to(m)

    # --- Fire districts ---
    if not layers["fire_districts"].empty:
        folium.GeoJson(
            _gdf_to_geojson(layers["fire_districts"]),
            name="Fire Districts",
            style_function=lambda x: LAYER_STYLES["district"],
            show=False,
        ).add_to(m)

    # --- Fire first due zones ---
    if not layers["fire_first_due"].empty:
        folium.GeoJson(
            _gdf_to_geojson(layers["fire_first_due"]),
            name="Fire First Due Zones",
            style_function=lambda x: {"color": "#9b59b6", "weight": 1,
                                       "fillOpacity": 0.05, "fillColor": "#9b59b6"},
            show=False,
        ).add_to(m)

    # --- WUI layer (color by class) ---
    if not layers["wui"].empty:
        wui = layers["wui"].copy()
        high_wui   = wui[wui["wuiclass2020"].isin(["High_Dens_Intermix", "High_Dens_Interface",
                                                    "Med_Dens_Intermix",  "Med_Dens_Interface"])]
        low_wui    = wui[wui["wuiclass2020"].isin(["Low_Dens_Intermix", "Low_Dens_Interface",
                                                   "Very_Low_Dens_Veg"])]

        if not high_wui.empty:
            folium.GeoJson(
                _gdf_to_geojson(high_wui),
                name="WUI — High/Med Risk",
                style_function=lambda x: LAYER_STYLES["wui_high"],
                tooltip=folium.GeoJsonTooltip(fields=["wuiclass2020"], aliases=["WUI Class:"]),
            ).add_to(m)

        if not low_wui.empty:
            folium.GeoJson(
                _gdf_to_geojson(low_wui),
                name="WUI — Low Risk",
                style_function=lambda x: LAYER_STYLES["wui_low"],
                show=False,
                tooltip=folium.GeoJsonTooltip(fields=["wuiclass2020"], aliases=["WUI Class:"]),
            ).add_to(m)

    # --- Fire perimeters ---
    all_perims = pd.concat([
        layers["fire_perimeters_usda"],
        layers["nifc_perimeters"],
    ]).pipe(gpd.GeoDataFrame, crs="EPSG:4326")

    if not all_perims.empty:
        folium.GeoJson(
            _gdf_to_geojson(all_perims),
            name="Historical Fire Perimeters",
            style_function=lambda x: LAYER_STYLES["fire_perim"],
            show=False,
        ).add_to(m)

    # --- Fire occurrence points ---
    if not layers["fire_occurrence"].empty:
        fire_group = folium.FeatureGroup(name="Fire Occurrence Points", show=False)
        for _, row in layers["fire_occurrence"].iterrows():
            if row.geometry:
                folium.CircleMarker(
                    location=[row.geometry.y, row.geometry.x],
                    radius=3,
                    color="#e74c3c",
                    fill=True,
                    fill_opacity=0.6,
                    popup=str(row.get("fire_name", row.get("FIRE_NAME", "Fire"))),
                ).add_to(fire_group)
        fire_group.add_to(m)

    # --- Fire stations ---
    if not layers["fire_stations"].empty:
        station_group = folium.FeatureGroup(name="Fire Stations")
        for _, row in layers["fire_stations"].iterrows():
            if row.geometry:
                folium.Marker(
                    location=[row.geometry.y, row.geometry.x],
                    icon=folium.Icon(color="red", icon="fire", prefix="fa"),
                    popup=f"<b>{row.get('Name','Station')}</b><br>{row.get('Address','')}",
                    tooltip=row.get("Name", "Fire Station"),
                ).add_to(station_group)
        station_group.add_to(m)

    # --- Custom risk score choropleth (expansion areas) ---
    scored_clean = scored.copy()
    scored_clean["risk_label"] = scored_clean["risk_label"].astype(str)

    risk_layer = folium.GeoJson(
        _gdf_to_geojson(scored_clean),
        name="🔥 UGB Expansion Risk Index",
        style_function=_risk_style,
        highlight_function=lambda x: {"weight": 4, "fillOpacity": 0.9},
        popup=folium.GeoJsonPopup(
            fields=["NAME", "risk_score", "risk_label", "ACRES",
                    "wui_score", "fire_density", "dist_to_station_mi",
                    "burn_acres", "in_city", "PLAN_TYPE"],
            aliases=["Area", "Risk Score", "Risk Level", "Acres",
                     "WUI Score", "Fire Incidents", "Dist. to Station (mi)",
                     "Burn Acres", "Inside City", "Plan Type"],
            localize=True,
        ),
        tooltip=folium.GeoJsonTooltip(
            fields=["NAME", "risk_score", "risk_label"],
            aliases=["Area:", "Score:", "Level:"],
        ),
    )
    risk_layer.add_to(m)

    # --- Legend ---
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: white; padding: 14px 18px; border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.35); font-family: Arial;
                font-size: 13px; max-width: 260px;">
        <b style="font-size:15px; color:#2c3e50">🏘️ UGB Expansion Areas</b>
        <div style="font-size:11px; color:#7f8c8d; margin:2px 0 10px 0;">
            Each filled block is a named expansion area, shaded by its composite
            wildfire-risk score. Click a block for details.
        </div>
        <div style="border-top:1px solid #ecf0f1; padding-top:8px;">
            <b style="font-size:12px; color:#2c3e50">Risk Level</b><br><br>
            <span style="background:#2ecc71; padding:3px 12px; border-radius:3px; color:white">Low</span>&nbsp;
            <span style="background:#f39c12; padding:3px 12px; border-radius:3px; color:white">Moderate</span><br><br>
            <span style="background:#e74c3c; padding:3px 12px; border-radius:3px; color:white">High</span>&nbsp;
            <span style="background:#8e1a0e; padding:3px 12px; border-radius:3px; color:white">Very High</span>
        </div>
        <div style="border-top:1px solid #ecf0f1; margin-top:10px; padding-top:8px;">
            <span style="display:inline-block; width:22px; border-top:3px dashed #f1c40f;
                         vertical-align:middle;"></span>
            <span style="font-size:11px; color:#2c3e50; vertical-align:middle;">
                Deschutes County limit</span><br>
            <span style="display:inline-block; width:22px; border-top:2px solid #2c3e50;
                         vertical-align:middle;"></span>
            <span style="font-size:11px; color:#2c3e50; vertical-align:middle;">
                Urban Growth Boundary</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Controls
    MiniMap(toggle_display=True).add_to(m)
    MeasureControl(primary_length_unit="miles").add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    # Focus the initial view on the expansion areas (with padding), not the whole county
    if not scored.empty:
        minx, miny, maxx, maxy = scored.total_bounds
        pad_x = (maxx - minx) * 0.15
        pad_y = (maxy - miny) * 0.15
        m.fit_bounds([[miny - pad_y, minx - pad_x], [maxy + pad_y, maxx + pad_x]])

    return m
