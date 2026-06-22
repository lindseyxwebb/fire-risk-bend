# 🔥 Bend, OR — Wildfire Risk & Urban Growth Analysis

An interactive GIS web application that scores wildfire risk across the Urban
Growth Boundary (UGB) expansion areas of Bend, Oregon — built to support
residential development site-selection and insurance-risk decisions.

**Live app:** _(add your Streamlit Cloud URL here after deploying)_

---

## The Problem

Homebuilders developing at the urban fringe face rising exposure to wildfire
risk. In Oregon's Wildland-Urban Interface (WUI), insurers have raised premiums
40–300% since 2020 — and in the highest-risk zones, have stopped writing
policies altogether. Bend is one of the fastest-growing cities in Oregon and
sits directly in the ponderosa-pine / high-desert interface, making it a prime
case study.

This app answers a practical question for a homebuilder or planner:

> **Which UGB expansion areas carry the most wildfire risk, and what does that
> mean for insurability?**

---

## What It Does

- Loads 18 live GIS layers from federal, state, and county REST services
- Clips all layers to Deschutes County
- Computes a **composite wildfire-risk score (0–10)** for each named UGB
  expansion area
- Renders an **interactive map** with toggleable layers and a risk choropleth
- Charts the risk ranking, an estimated insurance-cost relationship, and a
  factor-by-factor breakdown

## Risk Score Methodology

Each expansion area is scored on five weighted factors, chosen to mirror how
insurers assess property risk:

| Factor | Weight | Source |
|---|---|---|
| WUI classification (fuel + structure intermix) | 30% | USDA WUI 2020 |
| Fire incident density (within 3 miles) | 25% | USDA / Oregon fire history |
| Historical burn-scar overlap | 20% | USDA + NIFC perimeters |
| Distance to nearest fire station / response | 15% | Bend Fire + city limits |
| Social vulnerability | 10% | Oregon Explorer SVI |

> ⚠️ Insurance premium figures are **estimates** based on published Oregon WUI
> market data, used to illustrate the risk relationship. They are not quotes.

---

## Tech Stack

- **Python** — geopandas, shapely, pandas
- **Folium** — interactive Leaflet map
- **Plotly** — interactive charts
- **Streamlit** — web app framework + hosting

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app pulls all data live from public ArcGIS REST endpoints — no local data
files required.

## Project Structure

```
fire-risk-bend/
├── app.py                  # Streamlit app entry point
├── risk_score.py           # Composite risk-score logic
├── data/
│   └── layers.py           # All REST endpoint URLs
├── utils/
│   ├── loader.py           # Loads & clips all layers
│   ├── map_builder.py      # Builds the Folium map
│   └── chart_builder.py    # Builds the Plotly charts
└── requirements.txt
```

---

## Data Sources

All layers are accessed live via public ArcGIS REST services. Each source below
links to its data portal; the exact REST endpoints used are in
[`data/layers.py`](data/layers.py).

**Source portals:** [City of Bend Open Data](https://data.bendoregon.gov) ·
[Bend Fire & Rescue Data Hub](https://firedata-bendoregon.hub.arcgis.com/) ·
[Bend Data Viewer](https://experience.arcgis.com/experience/128a35de90b0404f98073897eb4b1610/page/Page?views=Map-Layers) ·
[Oregon Explorer Wildfire Viewer](https://oregon-explorer.apps.geocortex.com/webviewer/?app=fccd4dfc5a974213aa1fa6a01b9c07e1) ·
[NIFC Open Data](https://data-nifc.opendata.arcgis.com/) ·
[Oregon GeoHub](https://geohub.oregon.gov/)

### Boundaries & Growth
- [**Deschutes County boundary**](https://geohub.oregon.gov/datasets/oregon-geo::county-boundaries/about) — Oregon GeoHub / City of Bend GIS
- [**Urban Growth Boundary (statewide)**](https://services8.arcgis.com/8PAo5HGmvRMlF2eU/arcgis/rest/services/UGB_2022/FeatureServer/0) — Oregon Dept. of Land Conservation & Development (DLCD)
- [**UGB Expansion Areas**](https://data.bendoregon.gov/datasets/bendoregon::ugb-expansion-areas/explore) & [**Special Planned Districts**](https://services5.arcgis.com/JisFYcK2mIVg9ueP/arcgis/rest/services/Special_Planned_Districts/FeatureServer/0) — City of Bend GIS
- [**City Limits**](https://geohub-oregon-geo.hub.arcgis.com/datasets/oregon-geo::city-limits/about) — Oregon GeoHub / City of Bend GIS

### Wildland-Urban Interface
- [**WUI 2020**](https://usfs.maps.arcgis.com/home/item.html?id=454bddfa18784660a472685ac7965881) — USDA Forest Service, SILVIS Lab

### Fire Risk & History
- [**Fire Occurrence (6th Edition, 1992–2020)**](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrence6thEdition_01/MapServer/0) — USDA Forest Service
- [**Fire Occurrence & Perimeters (2016–2024)**](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceAndPerimeter_01/MapServer/10) — USDA Forest Service
- [**Historic Fire Perimeters (2000–2018)**](https://data-nifc.opendata.arcgis.com/) — National Interagency Fire Center (NIFC)
- [**Oregon Fire History (1992–2021)**](https://oregon-explorer.apps.geocortex.com/webviewer/?app=fccd4dfc5a974213aa1fa6a01b9c07e1) — Oregon Explorer
- [**CWPP Planning Areas**](https://oregon-explorer.apps.geocortex.com/webviewer/?app=fccd4dfc5a974213aa1fa6a01b9c07e1) — Oregon Explorer
- [**Burn Probability (tile overlay)**](https://oregon-explorer.apps.geocortex.com/webviewer/?app=fccd4dfc5a974213aa1fa6a01b9c07e1) — Oregon Explorer / PNW QWRA 2023

### Fire Protection
- [**Bend Fire Stations**](https://firedata-bendoregon.hub.arcgis.com/) — Bend Fire & Rescue
- [**Structural Fire Districts**](https://services.arcgis.com/uUvqNMGPm7axC2dD/arcgis/rest/services/Structural_Fire_Districts_Public/FeatureServer/68) — Oregon State Fire Marshal
- [**Ambulance Service Area**](https://maps.deschutes.org/arcgis/rest/services/911/FireMap/MapServer/6) & [**Fire First-Due Zones**](https://maps.deschutes.org/arcgis/rest/services/OpenData/BoundaryFD/MapServer/21) — Deschutes County GIS

### Population & Vulnerability
- [**Social Vulnerability Index (block groups)**](https://oregon-explorer.apps.geocortex.com/webviewer/?app=fccd4dfc5a974213aa1fa6a01b9c07e1) — Oregon Explorer / CDC SVI
- [**Community Wildfire Defense Grants**](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_CommWildfireDefenseGrant_01/MapServer/0) — USDA Forest Service

---

## About

Built as a portfolio project demonstrating live-data GIS pipelines, spatial
analysis, composite indexing, and interactive web mapping in Python.
