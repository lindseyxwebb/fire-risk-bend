"""Bend, OR Fire Risk & Urban Growth App — Portfolio project."""

import streamlit as st
from streamlit_folium import st_folium
from utils.loader import load_county, load_all
from risk_score import score_expansion_areas
from utils.map_builder import build_map
from utils.chart_builder import risk_bar_chart, insurance_estimate_chart, risk_factor_breakdown

st.set_page_config(
    page_title="Bend Fire Risk & Urban Growth",
    page_icon="🔥",
    layout="wide",
)

st.title("Bend, OR — Wildfire Risk & Urban Growth Analysis")
st.caption(
    "Analyzing fire risk in UGB expansion areas for residential development — "
    "Deschutes County, Oregon"
)

@st.cache_data(show_spinner="Loading spatial layers — first run takes ~60 seconds...")
def get_data():
    county = load_county()
    layers = load_all(county)
    scored = score_expansion_areas(layers)
    return county, layers, scored

county, layers, scored = get_data()

# --- Summary metrics ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Expansion Areas", len(scored))
col2.metric("High / Very High Risk", int((scored["risk_label"].isin(["High", "Very High"])).sum()))
col3.metric("Avg Distance to Station", f"{scored['dist_to_station_mi'].mean():.1f} mi")
col4.metric("Total Expansion Acres", f"{scored['ACRES'].sum():,.0f}")

st.divider()

# --- Map ---
st.subheader("Interactive Risk Map")
st.caption("Click any expansion area for detailed risk breakdown. Toggle layers in the top-right panel.")

m = build_map(layers, scored, county)
st_folium(m, use_container_width=True, height=600, returned_objects=[])

st.divider()

# --- Charts ---
st.subheader("Risk Score Analysis")

st.markdown("##### 📊 Risk Score Ranking")
st.plotly_chart(risk_bar_chart(scored), use_container_width=True)
st.caption(
    "Composite score (0–10) weighted across WUI classification, fire incident history, "
    "burn scar overlap, fire station response distance, and social vulnerability."
)

st.markdown("##### 💰 Insurance Cost Estimate")
st.plotly_chart(insurance_estimate_chart(scored), use_container_width=True)
st.caption(
    "Estimated annual homeowner insurance premiums based on published Oregon WUI market data. "
    "High-risk WUI properties in Oregon have seen significant premium increases in recent years."
)

st.markdown("##### 🧩 Factor Breakdown")
st.plotly_chart(risk_factor_breakdown(scored), use_container_width=True)
st.caption(
    "Each bar shows the weighted contribution of individual risk factors. "
    "WUI classification (30%) and fire density (25%) drive the largest share of risk."
)

st.divider()

# --- Data table ---
with st.expander("View raw risk score data"):
    display_cols = ["NAME", "ACRES", "risk_score", "risk_label",
                    "wui_score", "fire_density", "dist_to_station_mi",
                    "burn_acres", "in_city", "PLAN_TYPE"]
    available = [c for c in display_cols if c in scored.columns]
    st.dataframe(
        scored[available].sort_values("risk_score", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

# --- Data sources ---
with st.expander("📚 Data Sources & Methodology"):
    st.markdown(
        """
        All layers are accessed live via public ArcGIS REST services.

        **Boundaries & Growth**
        - [Deschutes County boundary](https://geohub.oregon.gov/datasets/oregon-geo::county-boundaries/about) — *Oregon GeoHub / City of Bend GIS*
        - [Urban Growth Boundary (statewide)](https://services8.arcgis.com/8PAo5HGmvRMlF2eU/arcgis/rest/services/UGB_2022/FeatureServer/0) — *Oregon DLCD*
        - [UGB Expansion Areas](https://data.bendoregon.gov/datasets/bendoregon::ugb-expansion-areas/explore) & [Special Planned Districts](https://services5.arcgis.com/JisFYcK2mIVg9ueP/arcgis/rest/services/Special_Planned_Districts/FeatureServer/0) — *City of Bend GIS*
        - [City Limits](https://geohub-oregon-geo.hub.arcgis.com/datasets/oregon-geo::city-limits/about) — *Oregon GeoHub / City of Bend GIS*

        **Wildland-Urban Interface**
        - [WUI 2020](https://usfs.maps.arcgis.com/home/item.html?id=454bddfa18784660a472685ac7965881) — *USDA Forest Service, SILVIS Lab*

        **Fire Risk & History**
        - [Fire Occurrence (6th Ed., 1992–2020)](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrence6thEdition_01/MapServer/0) — *USDA Forest Service*
        - [Fire Occurrence & Perimeters (2016–2024)](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceAndPerimeter_01/MapServer/10) — *USDA Forest Service*
        - [Historic Fire Perimeters (2000–2018)](https://data-nifc.opendata.arcgis.com/) — *National Interagency Fire Center*
        - [Oregon Fire History (1992–2021)](https://oregon-explorer.apps.geocortex.com/webviewer/?app=fccd4dfc5a974213aa1fa6a01b9c07e1) — *Oregon Explorer*
        - [CWPP Planning Areas](https://oregon-explorer.apps.geocortex.com/webviewer/?app=fccd4dfc5a974213aa1fa6a01b9c07e1) — *Oregon Explorer*
        - [Burn Probability tile overlay](https://oregon-explorer.apps.geocortex.com/webviewer/?app=fccd4dfc5a974213aa1fa6a01b9c07e1) — *Oregon Explorer / PNW QWRA 2023*

        **Fire Protection**
        - [Bend Fire Stations](https://firedata-bendoregon.hub.arcgis.com/) — *Bend Fire & Rescue*
        - [Structural Fire Districts](https://services.arcgis.com/uUvqNMGPm7axC2dD/arcgis/rest/services/Structural_Fire_Districts_Public/FeatureServer/68) — *Oregon State Fire Marshal*
        - [Ambulance Service Area](https://maps.deschutes.org/arcgis/rest/services/911/FireMap/MapServer/6) & [Fire First-Due Zones](https://maps.deschutes.org/arcgis/rest/services/OpenData/BoundaryFD/MapServer/21) — *Deschutes County GIS*

        **Population & Vulnerability**
        - [Social Vulnerability Index (block groups)](https://oregon-explorer.apps.geocortex.com/webviewer/?app=fccd4dfc5a974213aa1fa6a01b9c07e1) — *Oregon Explorer / CDC SVI*
        - [Community Wildfire Defense Grants](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_CommWildfireDefenseGrant_01/MapServer/0) — *USDA Forest Service*

        ---
        **Risk score** is a weighted composite (0–10): WUI class (30%), fire
        density (25%), burn-scar history (20%), station distance/response (15%),
        and social vulnerability (10%).

        ⚠️ *Insurance premium figures are estimates based on published Oregon WUI
        market data, shown to illustrate the risk relationship. They are not quotes.*
        """
    )

