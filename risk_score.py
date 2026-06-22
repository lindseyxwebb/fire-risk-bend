"""
Compute a composite fire risk index (1-10) for each UGB expansion area.

Inputs per expansion area:
  - WUI class (dominant classification within polygon)
  - Fire history density (# of fire points within 3 miles)
  - Burn scar overlap (acres burned nearby historically)
  - Distance to nearest fire station (miles)
  - Inside/outside city limits (binary)
  - Social vulnerability score (avg SVI within polygon)

Weights are designed to reflect insurance pricing logic:
  proximity to fuel + ignition history + response capability + human exposure
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point


# ---------------------------------------------------------------------------
# WUI classification mapping → numeric risk
# ---------------------------------------------------------------------------
WUI_RISK = {
    "High_Dens_Intermix":    10,
    "High_Dens_Interface":   9,
    "Med_Dens_Intermix":     8,
    "Med_Dens_Interface":    7,
    "Low_Dens_Intermix":     6,
    "Low_Dens_Interface":    5,
    "Very_Low_Dens_Veg":     4,
    "Very_Low_Dens_NoVeg":   3,
    "Uninhabited_Veg":       2,
    "Uninhabited_NoVeg":     1,
    "Water":                 0,
}


def _dominant_wui_class(expansion_poly, wui: gpd.GeoDataFrame) -> float:
    """Return the highest WUI risk score for cells that intersect the expansion polygon."""
    intersecting = wui[wui.intersects(expansion_poly)]
    if intersecting.empty:
        return 1.0
    col = "wuiclass2020" if "wuiclass2020" in intersecting.columns else intersecting.columns[0]
    scores = intersecting[col].map(WUI_RISK).dropna()
    return float(scores.max()) if not scores.empty else 1.0


def _fire_point_density(expansion_poly, fire_points: gpd.GeoDataFrame, buffer_mi: float = 3.0) -> int:
    """Count fire occurrence points within buffer_mi of the expansion area."""
    if fire_points.empty:
        return 0
    # Buffer in degrees (~0.0145 deg per mile at this latitude)
    buf = expansion_poly.buffer(buffer_mi * 0.0145)
    return int(fire_points[fire_points.intersects(buf)].shape[0])


def _burn_scar_overlap_acres(expansion_poly, perimeters: gpd.GeoDataFrame) -> float:
    """Return total acres of historical burn scars overlapping the expansion area."""
    if perimeters.empty:
        return 0.0
    overlapping = perimeters[perimeters.intersects(expansion_poly)]
    if overlapping.empty:
        return 0.0
    acres_col = next((c for c in ["gisacres", "GIS_ACRES", "ACRES", "acres"] if c in overlapping.columns), None)
    if acres_col:
        return float(overlapping[acres_col].sum())
    # Fallback: estimate from geometry area (convert degrees² to acres approx)
    return float(overlapping.intersection(expansion_poly).area.sum() * 2.47e9)


def _distance_to_nearest_station_mi(expansion_poly, stations: gpd.GeoDataFrame) -> float:
    """Return distance in miles from expansion area centroid to nearest fire station."""
    if stations.empty:
        return 99.0
    # Reproject to Oregon State Plane (metres) for accurate distance
    proj = "EPSG:2992"
    centroid = gpd.GeoSeries([expansion_poly], crs="EPSG:4326").to_crs(proj).iloc[0].centroid
    stations_proj = stations.to_crs(proj)
    distances = stations_proj.geometry.distance(centroid) / 1609.34  # metres → miles
    return float(distances.min())


def _inside_city_limits(expansion_poly, city_limits: gpd.GeoDataFrame) -> bool:
    """Return True if expansion area centroid is inside city limits."""
    if city_limits.empty:
        return False
    centroid = expansion_poly.centroid
    return bool(city_limits[city_limits.contains(centroid)].shape[0] > 0)


def _avg_social_vulnerability(expansion_poly, svi: gpd.GeoDataFrame) -> float:
    """Return average overall SVI score for block groups intersecting the expansion area."""
    if svi.empty:
        return 0.5
    intersecting = svi[svi.intersects(expansion_poly)]
    if intersecting.empty:
        return 0.5
    # Look for overall SVI score column
    svi_col = next((c for c in intersecting.columns if "svi" in c.lower() or "overall" in c.lower()), None)
    if svi_col:
        vals = pd.to_numeric(intersecting[svi_col], errors="coerce").dropna()
        return float(vals.mean()) if not vals.empty else 0.5
    return 0.5


def _normalize(value: float, min_val: float, max_val: float) -> float:
    """Scale a value to 0-10."""
    if max_val == min_val:
        return 5.0
    return float(np.clip((value - min_val) / (max_val - min_val) * 10, 0, 10))


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------
WEIGHTS = {
    "wui_score":          0.30,  # fuel + structure intermix
    "fire_density_score": 0.25,  # historical ignition frequency
    "burn_scar_score":    0.20,  # actual past burn exposure
    "response_score":     0.15,  # how far is help?
    "svi_score":          0.10,  # human vulnerability
}


def score_expansion_areas(layers: dict) -> gpd.GeoDataFrame:
    """
    Join all risk inputs to expansion areas and return a scored GeoDataFrame.
    Each row is one named expansion area with a composite risk_score (1-10).
    """
    expansion = layers["expansion_areas"].copy()

    # Combine all fire point layers
    fire_pts = pd.concat([
        layers["fire_occurrence"],
        layers["oregon_fire_history"],
    ]).pipe(gpd.GeoDataFrame, crs="EPSG:4326") if not layers["fire_occurrence"].empty else layers["oregon_fire_history"]

    # Combine all burn scar perimeter layers
    perims = pd.concat([
        layers["fire_perimeters_usda"],
        layers["nifc_perimeters"],
    ]).pipe(gpd.GeoDataFrame, crs="EPSG:4326") if not layers["fire_perimeters_usda"].empty else layers["nifc_perimeters"]

    records = []
    for _, row in expansion.iterrows():
        poly = row.geometry
        if poly is None or poly.is_empty:
            continue

        wui_raw       = _dominant_wui_class(poly, layers["wui"])
        density_raw   = _fire_point_density(poly, fire_pts)
        burn_raw      = _burn_scar_overlap_acres(poly, perims)
        dist_mi       = _distance_to_nearest_station_mi(poly, layers["fire_stations"])
        in_city       = _inside_city_limits(poly, layers["city_limits"])
        svi_raw       = _avg_social_vulnerability(poly, layers["social_vulnerability"])

        records.append({
            "NAME":         row.get("NAME", row.get("name", "Unknown")),
            "PLAN_TYPE":    row.get("PLAN_TYPE", ""),
            "ACRES":        row.get("ACRES", row.get("acres", 0)),
            "geometry":     poly,
            "wui_raw":      wui_raw,
            "fire_density": density_raw,
            "burn_acres":   burn_raw,
            "dist_to_station_mi": dist_mi,
            "in_city":      in_city,
            "svi_raw":      svi_raw,
        })

    df = pd.DataFrame(records)

    # Normalize each input to 0-10
    df["wui_score"]          = df["wui_raw"]
    df["fire_density_score"] = df["fire_density"].apply(
        lambda x: _normalize(x, df["fire_density"].min(), df["fire_density"].max())
    )
    df["burn_scar_score"]    = df["burn_acres"].apply(
        lambda x: _normalize(x, df["burn_acres"].min(), df["burn_acres"].max())
    )
    # Response: further = higher risk (invert distance)
    df["response_score"]     = df["dist_to_station_mi"].apply(
        lambda x: _normalize(x, df["dist_to_station_mi"].min(), df["dist_to_station_mi"].max())
    )
    # Outside city limits adds +1 to response risk
    df["response_score"]     = (df["response_score"] + df["in_city"].apply(lambda x: 0 if x else 1)).clip(0, 10)
    df["svi_score"]          = df["svi_raw"].apply(
        lambda x: _normalize(x, df["svi_raw"].min(), df["svi_raw"].max())
    )

    # Weighted composite score
    df["risk_score"] = (
        df["wui_score"]          * WEIGHTS["wui_score"]          +
        df["fire_density_score"] * WEIGHTS["fire_density_score"] +
        df["burn_scar_score"]    * WEIGHTS["burn_scar_score"]    +
        df["response_score"]     * WEIGHTS["response_score"]     +
        df["svi_score"]          * WEIGHTS["svi_score"]
    ).round(2)

    df["risk_label"] = pd.cut(
        df["risk_score"],
        bins=[0, 3, 5, 7, 10],
        labels=["Low", "Moderate", "High", "Very High"],
    )

    return gpd.GeoDataFrame(df, crs="EPSG:4326")
