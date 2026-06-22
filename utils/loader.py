"""Load and prepare all spatial layers, clipped to Deschutes County."""

import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union
from data.layers import *
import requests

TARGET_CRS = "EPSG:4326"


def load_county() -> gpd.GeoDataFrame:
    print("Loading county boundary...")
    return gpd.read_file(COUNTY_BOUNDARY).to_crs(TARGET_CRS)


def _esri_json_to_gdf(url: str) -> gpd.GeoDataFrame:
    """Load an Esri JSON endpoint (f=json) that doesn't support f=geojson."""
    from shapely.geometry import shape
    r = requests.get(url.replace("f=geojson", "f=json"), timeout=30)
    data = r.json()
    features = data.get("features", [])
    wkid = data.get("spatialReference", {}).get("wkid", 4326)
    rows = []
    for f in features:
        attrs = f.get("attributes", {})
        geom = f.get("geometry")
        if geom:
            # Convert Esri polygon rings to shapely
            if "rings" in geom:
                from shapely.geometry import Polygon, MultiPolygon
                rings = geom["rings"]
                polys = [Polygon(r) for r in rings if len(r) >= 3]
                attrs["geometry"] = polys[0] if len(polys) == 1 else MultiPolygon(polys)
            elif "x" in geom:
                from shapely.geometry import Point
                attrs["geometry"] = Point(geom["x"], geom["y"])
        rows.append(attrs)
    gdf = gpd.GeoDataFrame(rows, crs=f"EPSG:{wkid}")
    return gdf


def _load_and_clip(url: str, county: gpd.GeoDataFrame, name: str) -> gpd.GeoDataFrame:
    print(f"Loading {name}...")
    county_valid = county.copy()
    county_valid["geometry"] = county_valid.geometry.make_valid()

    def _clip(gdf):
        try:
            return gpd.clip(gdf, county_valid)
        except Exception:
            # If clip fails due to invalid geometries, fix them first then retry
            gdf["geometry"] = gdf.geometry.make_valid()
            return gpd.clip(gdf, county_valid)

    try:
        gdf = gpd.read_file(url).to_crs(TARGET_CRS)
        gdf["geometry"] = gdf.geometry.make_valid()
        gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
        clipped = _clip(gdf)
        print(f"  {name}: {len(clipped)} features")
        return clipped
    except Exception as e:
        # Fallback: parse Esri JSON format (older servers don't support f=geojson)
        try:
            gdf = _esri_json_to_gdf(url).to_crs(TARGET_CRS)
            gdf["geometry"] = gdf.geometry.make_valid()
            gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
            clipped = _clip(gdf)
            print(f"  {name} (fallback): {len(clipped)} features")
            return clipped
        except Exception as e2:
            print(f"  WARNING: {name} failed — {e2}")
            return gpd.GeoDataFrame(geometry=[], crs=TARGET_CRS)


def _load_wui(bounds, county: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Load WUI via raw JSON to avoid intermittent geopandas parsing failures."""
    from shapely.geometry import shape
    print("Loading WUI 2020...")
    url = (
        f"{WUI_2020_BASE}&geometry={bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]}"
        .replace("f=geojson", "f=json")
    )
    try:
        r = requests.get(url, timeout=60)
        data = r.json()
        features = data.get("features", [])
        wkid = data.get("spatialReference", {}).get("wkid", 102100)
        rows = []
        for f in features:
            attrs = f.get("attributes", {})
            geom = f.get("geometry")
            if geom and "rings" in geom:
                from shapely.geometry import Polygon, MultiPolygon
                polys = [Polygon(ring) for ring in geom["rings"] if len(ring) >= 3]
                if polys:
                    attrs["geometry"] = polys[0] if len(polys) == 1 else MultiPolygon(polys)
            rows.append(attrs)
        rows = [r for r in rows if "geometry" in r]
        gdf = gpd.GeoDataFrame(rows, crs=f"EPSG:{wkid}").to_crs(TARGET_CRS)
        gdf["geometry"] = gdf.geometry.make_valid()
        gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
        county_valid = county.copy()
        county_valid["geometry"] = county_valid.geometry.make_valid()
        clipped = gpd.clip(gdf, county_valid)
        print(f"  WUI 2020: {len(clipped)} features")
        return clipped
    except Exception as e:
        print(f"  WARNING: WUI 2020 failed — {e}")
        return gpd.GeoDataFrame(geometry=[], crs=TARGET_CRS)


def load_all(county: gpd.GeoDataFrame) -> dict:
    """Load all vector layers and clip to county boundary."""
    layers = {}

    # City & growth
    layers["ugb_bend"]              = _load_and_clip(UGB_BEND, county, "UGB Bend")
    layers["city_limits"]           = _load_and_clip(CITY_LIMITS_BEND, county, "City Limits")
    layers["expansion_areas"]       = _load_and_clip(UGB_EXPANSION_AREAS, county, "UGB Expansion Areas")
    layers["special_districts"]     = _load_and_clip(SPECIAL_PLANNED_DISTRICTS, county, "Special Planned Districts")
    layers["ugb_2022"]              = _load_and_clip(UGB_2022_STATEWIDE, county, "UGB 2022 Statewide")

    # WUI — fetch as raw JSON to avoid intermittent geometry parsing failures
    b = county.total_bounds
    layers["wui"]                   = _load_wui(b, county)

    # Fire risk & history
    layers["fire_occurrence"]       = _load_and_clip(FIRE_OCCURRENCE_6TH, county, "Fire Occurrence 6th Ed")
    fire_perim_url = FIRE_PERIMETERS_USDA_BASE + f"&geometry={b[0]},{b[1]},{b[2]},{b[3]}"
    layers["fire_perimeters_usda"]  = _load_and_clip(fire_perim_url, county, "USDA Fire Perimeters")
    layers["nifc_perimeters"]       = _load_and_clip(NIFC_HISTORIC_PERIMETERS, county, "NIFC Historic Perimeters")
    layers["oregon_fire_history"]   = _load_and_clip(OREGON_FIRE_HISTORY, county, "Oregon Fire History")
    layers["cwpp"]                  = _load_and_clip(CWPP_PLANNING_AREAS, county, "CWPP Planning Areas")

    # Fire protection
    layers["fire_stations"]         = _load_and_clip(BEND_FIRE_STATIONS, county, "Bend Fire Stations")
    layers["fire_districts"]        = _load_and_clip(FIRE_DISTRICTS, county, "Fire Districts")
    layers["ambulance"]             = _load_and_clip(AMBULANCE_SERVICE_AREA, county, "Ambulance Service Area")
    layers["rural_fire_district"]   = _load_and_clip(RURAL_FIRE_DISTRICT, county, "Rural Fire District")
    layers["fire_first_due"]        = _load_and_clip(FIRE_FIRST_DUE, county, "Fire First Due Zones")

    # Population & vulnerability
    svi_url = SOCIAL_VULNERABILITY_BASE + f"&geometry={b[0]},{b[1]},{b[2]},{b[3]}"
    layers["social_vulnerability"]  = _load_and_clip(svi_url, county, "Social Vulnerability")
    layers["cwdg_grants"]           = _load_and_clip(CWDG_GRANTS, county, "CWDG Grants")

    return layers
