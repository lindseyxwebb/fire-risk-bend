"""All REST endpoint URLs organized by category."""

COUNTY_BOUNDARY = (
    "https://services1.arcgis.com/znO8Hz1SuVVohYhZ/arcgis/rest/services/"
    "County_Boundary/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
)

# --- City & Growth ---
UGB_BEND = (
    "https://services1.arcgis.com/znO8Hz1SuVVohYhZ/ArcGIS/rest/services/"
    "Urban_Growth_Boundary/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
)
CITY_LIMITS_BEND = (
    "https://services1.arcgis.com/znO8Hz1SuVVohYhZ/ArcGIS/rest/services/"
    "City_Limits/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
)
UGB_EXPANSION_AREAS = (
    "https://services5.arcgis.com/JisFYcK2mIVg9ueP/arcgis/rest/services/"
    "UGB_Expansion_Areas1/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
)
SPECIAL_PLANNED_DISTRICTS = (
    "https://services5.arcgis.com/JisFYcK2mIVg9ueP/arcgis/rest/services/"
    "Special_Planned_Districts/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
)
UGB_2022_STATEWIDE = (
    "https://services8.arcgis.com/8PAo5HGmvRMlF2eU/arcgis/rest/services/"
    "UGB_2022/FeatureServer/0/query?outFields=*&where=instName%3D%27Bend%27&f=geojson"
)
ODOT_CITY_LIMITS = (
    "https://gis.odot.state.or.us/arcgis1006/rest/services/transgis/catalog/"
    "MapServer/220/query?outFields=*&where=1%3D1&f=geojson"
)

# --- WUI ---
# WUI uses bounding box + inSR=4326 — state filter returns 500 on this server
# Bounding box is injected at load time via loader.py
WUI_2020_BASE = (
    "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_WUI_2020_01/"
    "MapServer/0/query"
    "?geometryType=esriGeometryEnvelope&inSR=4326"
    "&spatialRel=esriSpatialRelIntersects&outFields=*&f=geojson"
)

# --- Fire Risk & History ---
FIRE_OCCURRENCE_6TH = (
    "https://apps.fs.usda.gov/arcx/rest/services/EDW/"
    "EDW_FireOccurrence6thEdition_01/MapServer/0/query?outFields=*&where=STATE%3D%27OR%27&f=geojson"
)
# Layer 10 = Final Fire Perimeter (All Years)
FIRE_PERIMETERS_USDA_BASE = (
    "https://apps.fs.usda.gov/arcx/rest/services/EDW/"
    "EDW_FireOccurrenceAndPerimeter_01/MapServer/10/query"
    "?geometryType=esriGeometryEnvelope&inSR=4326"
    "&spatialRel=esriSpatialRelIntersects&outFields=*&f=geojson"
)
NIFC_HISTORIC_PERIMETERS = (
    "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/"
    "Historic_Geomac_Perimeters_Combined_2000_2018/FeatureServer/0/"
    "query?outFields=*&where=state%3D%27OR%27&f=geojson"
)
OREGON_FIRE_HISTORY = (
    "https://arcgis-prod.oregonexplorer.info/arcgis/rest/services/Wildfire/"
    "FireHistory_2022/MapServer/0/query?outFields=*&where=1%3D1&f=geojson"
)
CWPP_PLANNING_AREAS = (
    "https://services1.arcgis.com/CD5mKowwN6nIaqd8/arcgis/rest/services/"
    "library_bnd_or_cwpp_planning_areas_10_2024/FeatureServer/65/"
    "query?outFields=*&where=1%3D1&f=geojson"
)

# Tile overlay URLs (used directly in folium, not loaded via geopandas)
BURN_PROBABILITY_TILES = (
    "https://tiles.arcgis.com/tiles/CD5mKowwN6nIaqd8/arcgis/rest/services/"
    "project_wre_bp_tile_package/MapServer/tile/{z}/{y}/{x}"
)
FUEL_MODELS_TILES = (
    "https://arcgis-prod.oregonexplorer.info/arcgis/rest/services/Wildfire/"
    "project_cwpp_planning_tool_env_or_fuel_models_2023/MapServer/tile/{z}/{y}/{x}"
)

# --- Fire Protection ---
BEND_FIRE_STATIONS = (
    "https://services5.arcgis.com/JisFYcK2mIVg9ueP/arcgis/rest/services/"
    "Bend_Fire_Stations/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
)
FIRE_DISTRICTS = (
    "https://services.arcgis.com/uUvqNMGPm7axC2dD/arcgis/rest/services/"
    "Structural_Fire_Districts_Public/FeatureServer/68/"
    "query?outFields=*&where=1%3D1&f=geojson"
)
AMBULANCE_SERVICE_AREA = (
    "https://maps.deschutes.org/arcgis/rest/services/911/FireMap/"
    "MapServer/6/query?outFields=*&where=ASANAME%3D%27BEND%27&f=geojson"
)
RURAL_FIRE_DISTRICT = (
    "https://maps.deschutes.org/arcgis/rest/services/OpenData/BoundaryFD/"
    "MapServer/5/query?outFields=*&where=1%3D1&f=geojson"
)
FIRE_RESPONSE_AREAS = (
    "https://maps.deschutes.org/arcgis/rest/services/OpenData/BoundaryFD/"
    "MapServer/20/query?outFields=*&where=1%3D1&f=geojson"
)
FIRE_FIRST_DUE = (
    "https://maps.deschutes.org/arcgis/rest/services/OpenData/BoundaryFD/"
    "MapServer/21/query?outFields=*&where=1%3D1&f=geojson"
)

# --- Population & Vulnerability ---
# Social vulnerability uses bounding box — statewide layer too large
SOCIAL_VULNERABILITY_BASE = (
    "https://arcgis-prod.oregonexplorer.info/arcgis/rest/services/Wildfire/"
    "Social_Vulnerability_Census_Block_Groups/MapServer/0/query"
    "?geometryType=esriGeometryEnvelope&inSR=4326"
    "&spatialRel=esriSpatialRelIntersects&outFields=*&f=geojson"
)
CWDG_GRANTS = (
    "https://apps.fs.usda.gov/arcx/rest/services/EDW/"
    "EDW_CommWildfireDefenseGrant_01/MapServer/0/"
    "query?outFields=*&where=STATE%3D%27OR%27&f=geojson"
)
