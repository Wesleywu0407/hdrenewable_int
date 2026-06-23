"""Step 6 — Generate the 3 Trading Market Volatility charts as standalone HTML.

Loads the datasets from data/raw/ and writes interactive Plotly
charts to outputs/figures/.

Run: python scripts/06_generate_trading_charts.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
FIG_DIR = PROJECT_ROOT / "outputs" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

SOURCE_FOOTER = "Source: OpenElectricity API (openelectricity.org.au)"
TEMPLATE = "plotly_white"

def english_title(en: str) -> str:
    return en

def add_source_footer(fig: go.Figure, extra: str = "") -> None:
    text = SOURCE_FOOTER + (f"　|　{extra}" if extra else "")
    fig.add_annotation(
        text=text,
        xref="paper",
        yref="paper",
        x=0,
        y=-0.16,
        showarrow=False,
        font=dict(size=10, color="#888"),
        align="left",
    )

def save(fig: go.Figure, name: str) -> Path:
    path = FIG_DIR / name
    fig.write_html(path, include_plotlyjs="cdn")
    print(f"  wrote {name} ({path.stat().st_size / 1024:.0f} KB)")
    return path

def fig2_1_spot_heatmap() -> None:
    # Read Spot Prices
    df = pd.read_csv(RAW_DIR / "qld_spot_prices.csv", parse_dates=["interval"])
    
    # We'll calculate a heatmap for average price by Hour of Day and Day of Week
    df["hour"] = df["interval"].dt.hour
    df["weekday"] = df["interval"].dt.day_name()
    
    # Order weekdays
    cats = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df["weekday"] = pd.Categorical(df["weekday"], categories=cats, ordered=True)
    
    heatmap_data = df.pivot_table(index="weekday", columns="hour", values="price", aggfunc="mean")
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale="Inferno",
        hoverongaps=False,
        hovertemplate="Day: %{y}<br>Hour: %{x}:00<br>Avg Price: $%{z:.2f}/MWh<extra></extra>"
    ))
    
    fig.update_layout(
        template=TEMPLATE,
        title=english_title("Spot Price Volatility Heatmap (QLD, Hourly Average)"),
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        margin=dict(b=110),
    )
    add_source_footer(fig, "Averaged over the past 90 days")
    save(fig, "fig2_1_spot_heatmap.html")

def fig2_2_fcas_regulation() -> None:
    # Read Mock Regulation FCAS
    df = pd.read_csv(RAW_DIR / "fcas_regulation_mock.csv", parse_dates=["interval"])
    df = df.sort_values("interval")
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Prices on primary y-axis
    fig.add_trace(
        go.Scatter(x=df["interval"], y=df["raise_price"], name="Raise Price", line=dict(color="#e74c3c", width=2)),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=df["interval"], y=df["lower_price"], name="Lower Price", line=dict(color="#3498db", width=2)),
        secondary_y=False,
    )
    
    # Volumes on secondary y-axis (bar or dashed line)
    fig.add_trace(
        go.Scatter(x=df["interval"], y=df["raise_volume"], name="Raise Vol", line=dict(color="#e74c3c", dash="dot", width=1), opacity=0.6),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(x=df["interval"], y=df["lower_volume"], name="Lower Vol", line=dict(color="#3498db", dash="dot", width=1), opacity=0.6),
        secondary_y=True,
    )
    
    fig.update_layout(
        template=TEMPLATE,
        title=english_title("Regulation FCAS Prices & Volumes"),
        hovermode="x unified",
        margin=dict(b=110),
    )
    fig.update_yaxes(title_text="Price (AUD/MWh)", secondary_y=False)
    fig.update_yaxes(title_text="Enabled Volume (MW)", secondary_y=True)
    add_source_footer(fig, "Synthetic/Mock Data for UI design")
    save(fig, "fig2_2_fcas_regulation.html")

def fig2_3_fcas_contingency() -> None:
    # Read Mock Contingency FCAS
    df = pd.read_csv(RAW_DIR / "fcas_contingency_mock.csv")
    df = df.sort_values("interval")
    
    fig = go.Figure()
    
    services = ["fast_raise", "slow_raise", "delayed_raise", "fast_lower", "slow_lower", "delayed_lower"]
    labels = ["Fast Raise (6s)", "Slow Raise (60s)", "Delayed Raise (5m)", "Fast Lower", "Slow Lower", "Delayed Lower"]
    colors = ["#e74c3c", "#f39c12", "#f1c40f", "#3498db", "#2980b9", "#2c3e50"]
    
    for srv, lbl, col in zip(services, labels, colors):
        fig.add_trace(go.Bar(
            x=df["interval"],
            y=df[srv],
            name=lbl,
            marker_color=col
        ))
        
    fig.update_layout(
        template=TEMPLATE,
        title=english_title("Contingency FCAS Market Value Breakdown"),
        barmode="stack",
        xaxis_title="Month",
        yaxis_title="Market Value (Million AUD)",
        margin=dict(b=110),
    )
    add_source_footer(fig, "Synthetic/Mock Data for UI design")
    save(fig, "fig2_3_fcas_contingency.html")

def main() -> int:
    print("Generating trading charts -> outputs/figures/")
    fig2_1_spot_heatmap()
    fig2_2_fcas_regulation()
    fig2_3_fcas_contingency()
    print("Done.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
