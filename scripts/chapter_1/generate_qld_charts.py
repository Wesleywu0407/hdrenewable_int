"""Step 4 - Generate the QLD-specific analysis charts (Section 1.1).

Run: python -m scripts.chapter_1.generate_qld_charts
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from scripts.common.constants import FUEL_COLORS, GEN_GROUPS, REGION_COLORS, STACK_ORDER
from scripts.common.paths import FIG_DIR, PNG_DIR, RAW_DIR

FIG_DIR.mkdir(parents=True, exist_ok=True)
PNG_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATE = "plotly_white"





def save(fig: go.Figure, name: str, png_name: str | None = None) -> Path:
    path = FIG_DIR / name
    fig.write_html(path, include_plotlyjs="cdn")
    print(f"  wrote {name} ({path.stat().st_size / 1024:.0f} KB)")
    if png_name:
        png_path = PNG_DIR / png_name
        fig.write_image(png_path, width=1200, height=600, scale=2)
        print(f"  wrote {png_name} ({png_path.stat().st_size / 1024:.0f} KB)")
    return path


def order_groups(present: list[str]) -> list[str]:
    return [g for g in STACK_ORDER if g in present]


# --------------------------------------------------------------------------- #
# Fig 1.1.1 - QLD Renewable Share vs Peers
# --------------------------------------------------------------------------- #
def fig1_1_qld_renewable_share() -> None:
    path = RAW_DIR / "nem_renewable_share.csv"
    if not path.exists():
        print(f"WARNING: {path} not found.")
        return

    df = pd.read_csv(path, parse_dates=["interval"])
    # Filter to only QLD1 and NEM peers for comparison
    df = df[df["network_region"].isin(["QLD1", "NSW1", "VIC1", "SA1", "TAS1"])].copy()
    
    # Calculate renewable percentage per region, per month
    pivot = df.pivot_table(
        index=["interval", "network_region"], 
        columns="renewable", 
        values="value", 
        aggfunc="sum"
    ).reset_index()
    
    # In case a month doesn't have False or True
    for col in [False, True]:
        if col not in pivot.columns:
            pivot[col] = 0

    pivot["total"] = pivot[False] + pivot[True]
    pivot["renew_pct"] = (pivot[True] / pivot["total"]) * 100

    fig = go.Figure()
    for region in ["QLD1", "NSW1", "VIC1", "SA1", "TAS1"]:
        sub = pivot[pivot["network_region"] == region].sort_values("interval")
        fig.add_trace(
            go.Scatter(
                x=sub["interval"],
                y=sub["renew_pct"],
                name=region,
                mode="lines",
                line=dict(width=3, color=REGION_COLORS.get(region, "#999")),
            )
        )

    fig.update_layout(
        template=TEMPLATE,
        title="Renewable Generation Share: QLD vs NEM Peers",
        yaxis_title="Renewable Share (%)",
        xaxis_title="",
        hovermode="x unified",
        legend_title="Region",
        margin=dict(b=110),
    )
    fig.update_xaxes(tickformat="%Y-%m")

    save(fig, "fig1_1_qld_renewable_share.html", "fig1_1_qld_renewable_share.png")


# --------------------------------------------------------------------------- #
# Fig 1.1.2 - QLD Fuel Mix Evolution
# --------------------------------------------------------------------------- #
def fig1_2_qld_fuel_mix() -> None:
    path = RAW_DIR / "qld_fuel_mix_24m.csv"
    if not path.exists():
        print(f"WARNING: {path} not found.")
        return

    df = pd.read_csv(path, parse_dates=["interval"])
    df = df[df["fueltech_group"] != "battery"]
    df["fueltech_group"] = df["fueltech_group"].replace("battery_discharging", "battery")
    df = df[df["fueltech_group"].isin(GEN_GROUPS)].copy()
    df["value"] = df["value"].clip(lower=0)
    groups = order_groups(sorted(df["fueltech_group"].unique()))

    fig = go.Figure()
    for g in groups:
        sub = df[df["fueltech_group"] == g].sort_values("interval")
        fig.add_trace(
            go.Bar(
                x=sub["interval"],
                y=sub["value"],
                name=g,
                marker_color=FUEL_COLORS.get(g, "#999"),
            )
        )

    fig.update_layout(
        template=TEMPLATE,
        barmode="stack",
        title="QLD Generation Mix Evolution (Last 24 Months)",
        yaxis_title="Energy (MWh)",
        xaxis_title="",
        hovermode="x unified",
        legend_title="Fuel group",
        margin=dict(b=120),
    )
    fig.update_xaxes(tickformat="%Y-%m")

    save(fig, "fig1_2_qld_fuel_mix.html", "fig1_2_qld_fuel_mix.png")


# --------------------------------------------------------------------------- #
# Fig 1.1.3 - QLD Negative Spot-Price Frequency
# --------------------------------------------------------------------------- #
def fig1_3_qld_negative_prices() -> None:
    path = RAW_DIR / "qld_spot_prices.csv"
    if not path.exists():
        print(f"WARNING: {path} not found.")
        return

    df = pd.read_csv(path, parse_dates=["interval"])
    
    # Calculate frequency and magnitude per day.
    df["day"] = df["interval"].dt.to_period("D").dt.to_timestamp()
    daily_prices = df.groupby("day").agg(
        max_price=("price", "max"),
        min_price=("price", "min")
    ).reset_index()

    neg_df = df[df["price"] < 0]
    neg_hours = neg_df.groupby("day").size().reset_index(name="hours")

    daily_stats = pd.merge(daily_prices, neg_hours, on="day", how="left")
    daily_stats["hours"] = daily_stats["hours"].fillna(0)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(
            x=daily_stats["day"],
            y=daily_stats["hours"],
            marker_color="#e74c3c",
            name="Negative Price Hours"
        ),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Scatter(
            x=daily_stats["day"],
            y=daily_stats["max_price"],
            mode="lines",
            line=dict(color="#f39c12"),
            name="Max Price ($/MWh)"
        ),
        secondary_y=True,
    )
    
    fig.add_trace(
        go.Scatter(
            x=daily_stats["day"],
            y=daily_stats["min_price"],
            mode="lines",
            line=dict(color="#3498db"),
            name="Min Price ($/MWh)"
        ),
        secondary_y=True,
    )

    fig.update_layout(
        template=TEMPLATE,
        title="QLD Daily Spot-Price Extremes & Negative Frequency",
        xaxis_title="",
        hovermode="x unified",
        margin=dict(b=110),
    )
    fig.update_yaxes(title_text="Hours below $0/MWh", secondary_y=False)
    fig.update_yaxes(title_text="Price ($/MWh)", secondary_y=True)
    fig.update_xaxes(tickformat="%Y-%m-%d")

    save(fig, "fig1_3_qld_negative_prices.html", "fig1_3_qld_negative_prices.png")


def main() -> int:
    print("Generating QLD charts -> outputs/figures/")
    fig1_1_qld_renewable_share()
    fig1_2_qld_fuel_mix()
    fig1_3_qld_negative_prices()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
