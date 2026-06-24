#!/usr/bin/env python3
"""
Generate AI Data Center power demand charts (Chapter 3).
"""

import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "figures"
PNG_DIR = OUTPUT_DIR / "png"

# We use the same theme as the rest of the project
THEME = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#D8D2C0", family="sans-serif"),
    margin=dict(l=20, r=20, t=40, b=40),
)

def build_global_capacity_chart() -> go.Figure:
    # Actual data for 2024 Global Data Center Capacity (GW)
    regions = [
        "United States",
        "China",
        "European Union",
        "Japan and Korea",
        "India",
        "Other Asia Pacific",
        "United Kingdom",
        "Australia and New Zealand",
        "Africa",
        "Other North America",
    ]
    capacity_gw = [53.7, 31.9, 11.9, 6.6, 3.6, 3.1, 2.6, 1.6, 1.5, 1.5]
    
    # Reverse so largest is at the top of the horizontal bar chart
    regions.reverse()
    capacity_gw.reverse()
    
    # We highlight Australia & NZ
    colors = ["#D6A21D" if region == "Australia and New Zealand" else "#557C9D" for region in regions]

    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=capacity_gw,
        y=regions,
        orientation='h',
        marker_color=colors,
        text=[f"{val} GW" for val in capacity_gw],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Capacity: %{x} GW<extra></extra>"
    ))

    fig.update_layout(
        **THEME,
        title="2024 Global Data Center IT Capacity by Region (GW)",
        xaxis=dict(title="Capacity (GW)", gridcolor="rgba(239,232,210,0.08)"),
        yaxis=dict(title="", gridcolor="rgba(0,0,0,0)"),
        showlegend=False,
        annotations=[
            dict(
                text="Source: 2024 Industry Estimates",
                xref="paper", yref="paper",
                x=1.0, y=-0.15,
                showarrow=False,
                font=dict(size=10, color="rgba(216, 210, 192, 0.6)"),
                xanchor="right", yanchor="top"
            )
        ]
    )
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=80))
    
    return fig

def build_deficit_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    
    # Renewable Supply (Area)
    fig.add_trace(go.Scatter(
        x=df["Year"],
        y=df["Renewable_Supply_MW"],
        name="Renewable Supply",
        mode="lines",
        line=dict(color="#5D9C58", width=2),
        fill="tozeroy",
        fillcolor="rgba(93, 156, 88, 0.3)",
        hovertemplate="Renewable Supply: %{y:,.0f} MW<extra></extra>"
    ))
    
    # Baseline Grid Demand (Line)
    fig.add_trace(go.Scatter(
        x=df["Year"],
        y=df["Baseline_Grid_Demand_MW"],
        name="Baseline Grid Demand",
        mode="lines",
        line=dict(color="#557C9D", width=2, dash="dash"),
        hovertemplate="Baseline Demand: %{y:,.0f} MW<extra></extra>"
    ))
    
    # Total Demand including AI (Area)
    fig.add_trace(go.Scatter(
        x=df["Year"],
        y=df["Total_Demand_MW"],
        name="Total Demand (inc. AI)",
        mode="lines",
        line=dict(color="#E74C3C", width=2),
        hovertemplate="Total Demand: %{y:,.0f} MW<extra></extra>"
    ))
    
    # Highlight the deficit
    fig.add_trace(go.Scatter(
        x=df["Year"].tolist() + df["Year"][::-1].tolist(),
        y=df["Total_Demand_MW"].tolist() + df["Renewable_Supply_MW"][::-1].tolist(),
        fill='toself',
        fillcolor='rgba(231, 76, 60, 0.4)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        name="Green Energy Deficit",
        showlegend=True
    ))

    fig.update_layout(
        **THEME,
        title="Projected Energy Demand vs Renewable Supply (2025-2035)",
        xaxis=dict(title="Year", gridcolor="rgba(239,232,210,0.08)", tickmode="linear"),
        yaxis=dict(title="Capacity (MW)", gridcolor="rgba(239,232,210,0.08)", rangemode="tozero"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified",
        annotations=[
            dict(
                text="Source: Synthetic projection based on AEMO ISP & Global Industry Reports.<br>Methodology: Baseline grid demand (+200 MW/yr) and AI data center demand (+35% YoY)<br>against linear renewable supply growth (+1500 MW/yr + acceleration factor).",
                xref="paper", yref="paper",
                x=0.0, y=-0.15,
                showarrow=False,
                font=dict(size=10, color="rgba(216, 210, 192, 0.6)"),
                xanchor="left", yanchor="top",
                align="left"
            )
        ]
    )
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=100))
    return fig

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = DATA_DIR / "ai_demand_projections.csv"
    if not csv_path.exists():
        print(f"Error: {csv_path} not found. Run 07_fetch_ai_demand.py first.")
        return

    df = pd.read_csv(csv_path)

    print("Generating Figure 3.1 (Global Assessment)...")
    fig3_1 = build_global_capacity_chart()
    
    html_path_1 = OUTPUT_DIR / "fig3_1_global_assessment.html"
    png_path_1 = PNG_DIR / "fig3_1_global_assessment.png"
    
    fig3_1.write_html(html_path_1, include_plotlyjs="cdn", config={"displayModeBar": False})
    fig3_1.write_image(png_path_1, width=800, height=450, scale=2)
    
    # print("Generating Figure 3.2 (Deficit Chart)...")
    # fig3_2 = build_deficit_chart(df)
    # html_path_2 = OUTPUT_DIR / "fig3_2_ai_energy_deficit.html"
    # png_path_2 = PNG_DIR / "fig3_2_ai_energy_deficit.png"
    # fig3_2.write_html(html_path_2, include_plotlyjs="cdn", config={"displayModeBar": False})
    # fig3_2.write_image(png_path_2, width=800, height=450, scale=2)
    
    print("Done generating AI charts.")

if __name__ == "__main__":
    main()
