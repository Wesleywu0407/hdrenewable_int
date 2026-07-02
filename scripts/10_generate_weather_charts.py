"""Chapter 2.4 - Generate Weather & Market Price Correlation Charts.

Loads data/raw/weather_price_correlation.csv and creates two charts:
1. Temperature vs Demand vs Price (Time Series)
2. Solar Irradiance vs Negative Spot Prices (Scatter Plot)
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

INPUT_CSV = RAW_DIR / "weather_price_correlation.csv"
OUTPUT_HTML = FIG_DIR / "fig2_4_weather_correlation.html"

TEMPLATE = "plotly_white"


def english_title(en: str) -> str:
    return en



def main() -> int:
    if not INPUT_CSV.exists():
        print(f"ERROR: {INPUT_CSV} not found. Please run 09_fetch_weather_data.py first.")
        return 1
        
    print(f"Loading {INPUT_CSV}...")
    df = pd.read_csv(INPUT_CSV, parse_dates=["interval"])
    
    # 1. Temperature vs Demand vs Price (Time Series)
    # To avoid the chart being too cluttered, we'll plot a subset (e.g. the most recent 30 days)
    # or the entire dataset if preferred. The user can zoom in.
    
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=False,
        vertical_spacing=0.15,
        specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
        subplot_titles=(
            "Temperature vs Demand vs Spot Price (Time Series)",
            "Solar Irradiance vs Spot Price (Colored by Hour of Day)"
        )
    )

    # --- Chart 1: Time Series ---
    # Highlight extreme temperatures
    extreme_high = df[df["temperature_2m"] > 30]
    extreme_low = df[df["temperature_2m"] < 10]
    
    # Demand (Area chart, light blue)
    if "demand" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["interval"], y=df["demand"],
                name="Demand (MW)",
                mode="lines",
                fill="tozeroy",
                line=dict(color="lightblue", width=1),
                opacity=0.5
            ),
            row=1, col=1, secondary_y=False
        )
    
    # Spot Price (Scatter/Line, red)
    fig.add_trace(
        go.Scatter(
            x=df["interval"], y=df["price"],
            name="Spot Price (AUD)",
            mode="lines",
            line=dict(color="red", width=1)
        ),
        row=1, col=1, secondary_y=False
    )
    
    # Temperature (Line, orange)
    fig.add_trace(
        go.Scatter(
            x=df["interval"], y=df["temperature_2m"],
            name="Temperature (°C)",
            mode="lines",
            line=dict(color="orange", width=2)
        ),
        row=1, col=1, secondary_y=True
    )
    
    # Highlight points >30C
    fig.add_trace(
        go.Scatter(
            x=extreme_high["interval"], y=extreme_high["temperature_2m"],
            mode="markers", name="> 30°C",
            marker=dict(color="darkorange", size=6, symbol="triangle-up")
        ),
        row=1, col=1, secondary_y=True
    )

    # Highlight points <10C
    fig.add_trace(
        go.Scatter(
            x=extreme_low["interval"], y=extreme_low["temperature_2m"],
            mode="markers", name="< 10°C",
            marker=dict(color="blue", size=6, symbol="triangle-down")
        ),
        row=1, col=1, secondary_y=True
    )

    fig.update_yaxes(title_text="Demand (MW) / Price (AUD)", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Temperature (°C)", row=1, col=1, secondary_y=True)

    # --- Chart 2: Solar vs Price Scatter ---
    # Extract hour for color scaling
    df["hour"] = df["interval"].dt.hour
    
    # Filter negative spot prices for better visualization if desired, 
    # but the instructions say: "comparing Solar Irradiance against Spot Price. Color by time of day to show how high midday solar correlates with negative prices."
    
    fig.add_trace(
        go.Scatter(
            x=df["direct_radiation"],
            y=df["price"],
            mode="markers",
            marker=dict(
                size=6,
                color=df["hour"],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Hour of Day", x=1.05, y=0.22, len=0.45)
            ),
            text=df["interval"].dt.strftime("%Y-%m-%d %H:%M"),
            hovertemplate="Solar: %{x} W/m²<br>Price: $%{y}<br>Time: %{text}<extra></extra>",
            name="Solar vs Price"
        ),
        row=2, col=1
    )
    
    fig.update_xaxes(title_text="Direct Solar Radiation (W/m²)", row=2, col=1)
    fig.update_yaxes(title_text="Spot Price (AUD/MWh)", row=2, col=1)
    
    # To better show negative prices, we might add a horizontal line at y=0
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)

    fig.update_layout(
        template=TEMPLATE,
        title=english_title("Weather & Market Price Correlation"),
        height=900,
        hovermode="closest",
        margin=dict(b=80)
    )
    

    
    fig.write_html(OUTPUT_HTML, include_plotlyjs="cdn")
    print(f"  wrote fig2_4_weather_correlation.html ({OUTPUT_HTML.stat().st_size / 1024:.0f} KB)")
    
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
