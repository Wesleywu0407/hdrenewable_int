"""Step 4 — Generate the QLD-specific analysis charts (Section 1.1).

Run: python scripts/04_generate_qld_charts.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
FIG_DIR = PROJECT_ROOT / "outputs" / "figures"
PNG_DIR = FIG_DIR / "png"
FIG_DIR.mkdir(parents=True, exist_ok=True)
PNG_DIR.mkdir(parents=True, exist_ok=True)

# Shared style
FUEL_COLORS = {
    "coal": "#1a1a1a",
    "gas": "#e8722c",
    "solar": "#f4d03f",
    "wind": "#5dade2",
    "hydro": "#1f618d",
    "battery": "#27ae60",
    "bioenergy": "#7d6608",
    "distillate": "#a04000",
    "pumps": "#76448a",
    "other": "#909497",
}

REGION_COLORS = {
    "QLD1": "#8e44ad",
    "NSW1": "#3498db",
    "VIC1": "#2c3e50",
    "SA1": "#e74c3c",
    "TAS1": "#27ae60",
}

GEN_GROUPS = ["coal", "gas", "hydro", "wind", "solar", "bioenergy", "distillate", "battery"]
STACK_ORDER = ["coal", "gas", "distillate", "hydro", "wind", "solar", "bioenergy", "battery"]
SOURCE_FOOTER = "Source: OpenElectricity API (openelectricity.org.au)"
TEMPLATE = "plotly_white"


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
# Fig 1.1.1 — QLD Renewable Share vs Peers
# --------------------------------------------------------------------------- #
def fig1_1_qld_renewable_share() -> None:
    path = RAW_DIR / "nem_renewable_share.csv"
    if not path.exists():
        print(f"WARNING: {path} not found.")
        return

    df = pd.read_csv(path, parse_dates=["interval"])
    # Filter to only QLD1 and NSW1 for comparison
    df = df[df["network_region"].isin(["QLD1", "NSW1"])].copy()
    
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
    for region in ["QLD1", "NSW1"]:
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
        title="Renewable Generation Share: QLD vs NSW",
        yaxis_title="Renewable Share (%)",
        xaxis_title="",
        hovermode="x unified",
        legend_title="Region",
        margin=dict(b=110),
    )
    fig.update_xaxes(tickformat="%Y-%m")
    add_source_footer(fig)
    save(fig, "fig1_1_qld_renewable_share.html", "fig1_1_qld_renewable_share.png")


# --------------------------------------------------------------------------- #
# Fig 1.1.2 — QLD Fuel Mix Evolution
# --------------------------------------------------------------------------- #
def fig1_2_qld_fuel_mix() -> None:
    path = RAW_DIR / "qld_fuel_mix_24m.csv"
    if not path.exists():
        print(f"WARNING: {path} not found.")
        return

    df = pd.read_csv(path, parse_dates=["interval"])
    df = df[df["fueltech_group"].isin(GEN_GROUPS)].copy()
    df["value"] = df["value"].clip(lower=0)
    groups = order_groups(sorted(df["fueltech_group"].unique()))

    fig = go.Figure()
    for g in groups:
        sub = df[df["fueltech_group"] == g].sort_values("interval")
        fig.add_trace(
            go.Scatter(
                x=sub["interval"],
                y=sub["value"],
                name=g,
                mode="lines",
                stackgroup="one",
                line=dict(width=0.5, color=FUEL_COLORS.get(g, "#999")),
                fillcolor=FUEL_COLORS.get(g, "#999"),
            )
        )

    fig.update_layout(
        template=TEMPLATE,
        title="QLD Generation Mix Evolution (Last 24 Months)",
        yaxis_title="Energy (MWh)",
        xaxis_title="",
        hovermode="x unified",
        legend_title="Fuel group",
        margin=dict(b=120),
    )
    fig.update_xaxes(tickformat="%Y-%m")
    add_source_footer(fig)
    save(fig, "fig1_2_qld_fuel_mix.html", "fig1_2_qld_fuel_mix.png")


# --------------------------------------------------------------------------- #
# Fig 1.1.3 — QLD Negative Spot-Price Frequency
# --------------------------------------------------------------------------- #
def fig1_3_qld_negative_prices() -> None:
    path = RAW_DIR / "qld_spot_prices.csv"
    if not path.exists():
        print(f"WARNING: {path} not found.")
        return

    df = pd.read_csv(path, parse_dates=["interval"])
    
    # Filter only negative prices
    neg_df = df[df["price"] < 0].copy()
    
    # Count frequency per month. The interval is 1h, so count = hours.
    neg_df["month"] = neg_df["interval"].dt.to_period("M").dt.to_timestamp()
    monthly_counts = neg_df.groupby("month").size().reset_index(name="hours")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=monthly_counts["month"],
            y=monthly_counts["hours"],
            marker_color="#e74c3c",
            name="Negative Price Hours"
        )
    )

    fig.update_layout(
        template=TEMPLATE,
        title="QLD Negative Spot-Price Frequency",
        yaxis_title="Hours below $0/MWh",
        xaxis_title="",
        hovermode="x unified",
        margin=dict(b=110),
    )
    fig.update_xaxes(tickformat="%Y-%m")
    add_source_footer(fig, "Count of hourly spot prices < $0/MWh")
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
