"""Step 6 - Generate the 3 Trading Market Volatility charts as standalone HTML.

Loads the datasets from data/raw/ and writes interactive Plotly
charts to outputs/figures/.

Run: python -m scripts.chapter_2.generate_trading_charts
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from scripts.common.paths import FIG_DIR, PNG_DIR, RAW_DIR

FIG_DIR.mkdir(parents=True, exist_ok=True)
PNG_DIR.mkdir(parents=True, exist_ok=True)


TEMPLATE = "plotly_white"

def english_title(en: str) -> str:
    return en



def save(fig: go.Figure, name: str, png_name: str | None = None) -> Path:
    path = FIG_DIR / name
    fig.write_html(path, include_plotlyjs="cdn")
    print(f"  wrote {name} ({path.stat().st_size / 1024:.0f} KB)")
    if png_name:
        png_path = PNG_DIR / png_name
        fig.write_image(png_path, width=1200, height=600, scale=2)
        print(f"  wrote {png_name} ({png_path.stat().st_size / 1024:.0f} KB)")
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

    save(fig, "fig2_1_spot_heatmap.html", "fig2_1_spot_heatmap.png")

def fig2_2_fcas_regulation() -> None:
    # Read Regulation FCAS
    df = pd.read_csv(RAW_DIR / "fcas_regulation.csv", parse_dates=["interval"])
    df = df.sort_values("interval")
    
    # Resample to weekly average to reduce noise
    df = df.resample("W-MON", on="interval").mean().reset_index()
    
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
    
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all", label="All")
            ])
        )
    )
    if not df.empty:
        last_date = df["interval"].max()
        first_date = df["interval"].min()
        fig.update_xaxes(
            range=[(last_date - pd.Timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S'), last_date.strftime('%Y-%m-%d %H:%M:%S')],
            rangeslider=dict(visible=True, range=[first_date.strftime('%Y-%m-%d %H:%M:%S'), last_date.strftime('%Y-%m-%d %H:%M:%S')])
        )


    save(fig, "fig2_2_fcas_regulation.html", "fig2_2_fcas_regulation.png")

def fig2_3_fcas_contingency() -> None:
    # Read Contingency FCAS
    df = pd.read_csv(RAW_DIR / "fcas_contingency.csv", parse_dates=["interval"])
    df = df.sort_values("interval")
    
    # Resample to weekly sum for market value
    df = df.resample("W-MON", on="interval").sum(numeric_only=True).reset_index()
    
    fig = go.Figure()
    
    # Raise services (warm tones) — grouped together with legendgroup
    raise_services = [
        ("fast_raise",    "Fast Raise (6s)",     "#e74c3c"),
        ("slow_raise",    "Slow Raise (60s)",     "#f39c12"),
        ("delayed_raise", "Delayed Raise (5m)",   "#f1c40f"),
    ]
    # Lower services (cool tones) — grouped together with legendgroup
    lower_services = [
        ("fast_lower",    "Fast Lower (6s)",      "#3498db"),
        ("slow_lower",    "Slow Lower (60s)",      "#2980b9"),
        ("delayed_lower", "Delayed Lower (5m)",    "#2c3e50"),
    ]

    for srv, lbl, col in raise_services:
        fig.add_trace(go.Bar(
            x=df["interval"],
            y=df[srv],
            name=lbl,
            marker_color=col,
            legendgroup="raise",
            legendgrouptitle_text="Raise",
            offsetgroup="raise",
        ))

    for srv, lbl, col in lower_services:
        fig.add_trace(go.Bar(
            x=df["interval"],
            y=df[srv],
            name=lbl,
            marker_color=col,
            legendgroup="lower",
            legendgrouptitle_text="Lower",
            offsetgroup="lower",
        ))
        
    fig.update_layout(
        template=TEMPLATE,
        title=english_title("Contingency FCAS Market Value Breakdown (Raise vs Lower)"),
        barmode="stack",
        bargroupgap=0.08,
        xaxis_title="Week",
        yaxis_title="Market Value (Million AUD)",
        margin=dict(b=110),
        legend=dict(
            groupclick="toggleitem",
            tracegroupgap=12,
        ),
    )
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all", label="All")
            ])
        )
    )
    if not df.empty:
        last_date = df["interval"].max()
        first_date = df["interval"].min()
        fig.update_xaxes(
            range=[(last_date - pd.Timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S'), last_date.strftime('%Y-%m-%d %H:%M:%S')],
            rangeslider=dict(visible=True, range=[first_date.strftime('%Y-%m-%d %H:%M:%S'), last_date.strftime('%Y-%m-%d %H:%M:%S')])
        )

    save(fig, "fig2_3_fcas_contingency.html", "fig2_3_fcas_contingency.png")


def main() -> int:
    print("Generating trading charts -> outputs/figures/")
    fig2_1_spot_heatmap()
    fig2_2_fcas_regulation()
    fig2_3_fcas_contingency()
    print("Done.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
