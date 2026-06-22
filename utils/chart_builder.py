"""Build interactive Plotly charts for the risk score dashboard."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

RISK_COLORS = {
    "Low":       "#2ecc71",
    "Moderate":  "#f39c12",
    "High":      "#e74c3c",
    "Very High": "#8e1a0e",
}

# Dark theme shared across all charts
BG = "#111111"
TEXT = "#ffffff"
GRID = "#333333"


def _apply_dark_theme(fig, title: str, yaxis_title=None, xaxis_title=None):
    """Apply a consistent black background / white text theme."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=TEXT)),
        plot_bgcolor=BG,
        paper_bgcolor=BG,
        font=dict(family="Arial", size=13, color=TEXT),
        yaxis_title=yaxis_title,
        xaxis_title=xaxis_title,
    )
    fig.update_yaxes(showgrid=True, gridcolor=GRID, color=TEXT, zerolinecolor=GRID)
    fig.update_xaxes(color=TEXT, zerolinecolor=GRID)
    return fig

# Estimated average annual homeowner insurance premium by risk level
# Based on published Oregon/national data for WUI-adjacent properties
INSURANCE_ESTIMATES = {
    "Low":       1_800,
    "Moderate":  3_200,
    "High":      5_800,
    "Very High": 9_500,
}


def risk_bar_chart(scored) -> go.Figure:
    """Horizontal bar chart of expansion areas ranked by risk score."""
    df = scored.sort_values("risk_score", ascending=True).copy()
    df["risk_label"] = df["risk_label"].astype(str)
    df["color"] = df["risk_label"].map(RISK_COLORS)

    fig = go.Figure(go.Bar(
        x=df["risk_score"],
        y=df["NAME"],
        orientation="h",
        marker_color=df["color"],
        text=df["risk_score"].apply(lambda x: f"{x:.2f}"),
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Risk Score: %{x:.2f}<br>"
            "Fire Incidents: %{customdata[0]}<br>"
            "Dist. to Station: %{customdata[1]:.1f} mi<br>"
            "Acres: %{customdata[2]:,.0f}"
            "<extra></extra>"
        ),
        customdata=df[["fire_density", "dist_to_station_mi", "ACRES"]].values,
    ))

    fig.update_traces(textfont_color=TEXT)
    fig.update_layout(
        xaxis=dict(range=[0, 11]),
        height=500,
        margin=dict(l=20, r=60, t=50, b=40),
    )
    _apply_dark_theme(
        fig,
        title="UGB Expansion Areas — Composite Fire Risk Score",
        xaxis_title="Risk Score (0–10)",
    )
    fig.update_xaxes(showgrid=True, gridcolor=GRID)
    fig.update_yaxes(showgrid=False)

    return fig


def insurance_estimate_chart(scored) -> go.Figure:
    """Bar chart showing estimated annual insurance premium per expansion area."""
    df = scored.sort_values("risk_score", ascending=False).copy()
    df["risk_label"] = df["risk_label"].astype(str)
    df["est_premium"] = df["risk_label"].map(INSURANCE_ESTIMATES)
    df["color"] = df["risk_label"].map(RISK_COLORS)

    fig = go.Figure(go.Bar(
        x=df["NAME"],
        y=df["est_premium"],
        marker_color=df["color"],
        text=df["est_premium"].apply(lambda x: f"${x:,}"),
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Est. Annual Premium: $%{y:,}<br>"
            "Risk Level: %{customdata[0]}<br>"
            "Risk Score: %{customdata[1]:.2f}"
            "<extra></extra>"
        ),
        customdata=df[["risk_label", "risk_score"]].values,
    ))

    fig.update_traces(textfont_color=TEXT)
    fig.update_layout(
        yaxis=dict(tickprefix="$", tickformat=","),
        height=460,
        margin=dict(l=20, r=20, t=50, b=120),
        xaxis_tickangle=-35,
    )
    _apply_dark_theme(
        fig,
        title="Estimated Homeowner Insurance Premium by Expansion Area",
        yaxis_title="Est. Annual Premium (USD)",
    )
    fig.update_xaxes(showgrid=False)

    # Add annotation explaining source
    fig.add_annotation(
        text="* Estimates based on Oregon WUI insurance market data. Not a quote.",
        xref="paper", yref="paper",
        x=0, y=-0.32,
        showarrow=False,
        font=dict(size=10, color="#95a5a6"),
        align="left",
    )

    return fig


def risk_factor_breakdown(scored) -> go.Figure:
    """Stacked bar showing contribution of each factor to total score per area."""
    df = scored.sort_values("risk_score", ascending=False).copy()

    factors = {
        "WUI Score":       ("wui_score",          0.30),
        "Fire Density":    ("fire_density_score",  0.25),
        "Burn History":    ("burn_scar_score",     0.20),
        "Response Time":   ("response_score",      0.15),
        "Vulnerability":   ("svi_score",           0.10),
    }

    colors = ["#c0392b", "#e67e22", "#27ae60", "#2980b9", "#8e44ad"]
    fig = go.Figure()

    for (label, (col, weight)), color in zip(factors.items(), colors):
        if col in df.columns:
            contribution = df[col] * weight
            fig.add_trace(go.Bar(
                name=label,
                x=df["NAME"],
                y=contribution.round(2),
                marker_color=color,
                marker_line_color="white",
                marker_line_width=0.5,
                hovertemplate=f"<b>%{{x}}</b><br>{label}: %{{y:.2f}}<extra></extra>",
            ))

    fig.update_layout(
        barmode="stack",
        height=500,
        margin=dict(l=20, r=20, t=80, b=130),
        xaxis_tickangle=-35,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            font=dict(size=12, color=TEXT),
            bgcolor="rgba(0,0,0,0.4)",
            bordercolor=GRID,
            borderwidth=1,
        ),
    )
    _apply_dark_theme(
        fig,
        title="Risk Score Factor Breakdown by Expansion Area",
        yaxis_title="Score Contribution",
    )

    return fig
