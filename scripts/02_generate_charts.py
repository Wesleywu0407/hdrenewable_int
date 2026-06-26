"""Step 2 — Generate the 4 NEM analysis charts as standalone HTML.

Loads the 4 CSV datasets from data/raw/ and writes interactive Plotly
charts to outputs/figures/. English titles, consistent fuel
colors, plotly_white template.

Run: python scripts/02_generate_charts.py
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

# --------------------------------------------------------------------------- #
# Shared style
# --------------------------------------------------------------------------- #
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

REGION_LABELS = {
    "NSW1": "NSW",
    "QLD1": "QLD",
    "VIC1": "VIC",
    "SA1": "SA",
    "TAS1": "TAS",
}
REGION_ORDER = ["QLD1", "NSW1", "VIC1", "SA1", "TAS1"]

# Generation-side groups for stacked mixes. Excludes battery_charging/
# battery_discharging (these double-count net "battery") and pumps (a load).
GEN_GROUPS = ["coal", "gas", "hydro", "wind", "solar", "bioenergy", "distillate", "battery"]

# Stack order (bottom -> top): firm/fossil at the bottom, renewables on top.
STACK_ORDER = ["coal", "gas", "distillate", "hydro", "wind", "solar", "bioenergy", "battery"]

SOURCE_FOOTER = "Source: OpenElectricity API (openelectricity.org.au)"
TEMPLATE = "plotly_white"


def english_title(en: str) -> str:
    """Main English title."""
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


def order_groups(present: list[str]) -> list[str]:
    """Return groups in canonical stack order, keeping only those present."""
    return [g for g in STACK_ORDER if g in present]


# --------------------------------------------------------------------------- #
# Fig 1 — Real-time generation mix (past 7 days, 30-min)
# --------------------------------------------------------------------------- #
def fig1_realtime() -> None:
    # -- Read master wide-format CSV ---------------------------------------- #
    df = pd.read_csv(
        RAW_DIR / "master_NEM_open_electricity.csv", parse_dates=["date"]
    )

    # No date filter; use all data in the CSV

    # -- Mapping from wide MW columns to FUEL_COLORS keys ------------------- #
    WIDE_TO_FUEL = {
        "Coal (Brown) -  MW": "coal",
        "Coal (Black) -  MW": "coal",
        "Gas (Steam) -  MW": "gas",
        "Gas (CCGT) -  MW": "gas",
        "Gas (OCGT) -  MW": "gas",
        "Gas (Reciprocating) -  MW": "gas",
        "Gas (Waste Coal Mine) -  MW": "gas",
        "Solar (Utility) -  MW": "solar",
        "Solar (Rooftop) -  MW": "solar",
        "Wind -  MW": "wind",
        "Hydro -  MW": "hydro",
        "Battery (Discharging) -  MW": "battery",
        "Bioenergy (Biomass) -  MW": "bioenergy",
        "Distillate -  MW": "distillate",
    }

    # -- Extract price before melting --------------------------------------- #
    price_df = (
        df[["date", "Price - AUD/MWh"]]
        .dropna(subset=["Price - AUD/MWh"])
        .rename(columns={"Price - AUD/MWh": "value"})
        .sort_values("date")
    )

    # -- Melt only the MW power columns into long format -------------------- #
    mw_cols = [c for c in WIDE_TO_FUEL if c in df.columns]
    melted = pd.melt(
        df, id_vars=["date"], value_vars=mw_cols,
        var_name="fueltech_group", value_name="value",
    )
    melted["fueltech_group"] = melted["fueltech_group"].map(WIDE_TO_FUEL)
    melted["value"] = melted["value"].clip(lower=0)  # generation-only stack

    # -- Aggregate by fuel group (e.g. coal_brown + coal_black → coal) ------ #
    melted = (
        melted.groupby(["date", "fueltech_group"], as_index=False)["value"].sum()
    )
    groups = order_groups(sorted(melted["fueltech_group"].unique()))

    # -- Build chart -------------------------------------------------------- #
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for g in groups:
        sub = melted[melted["fueltech_group"] == g].sort_values("date")
        fig.add_trace(
            go.Scatter(
                x=sub["date"],
                y=sub["value"],
                name=g,
                mode="lines",
                stackgroup="one",
                line=dict(width=0.5, color=FUEL_COLORS.get(g, "#999")),
                fillcolor=FUEL_COLORS.get(g, "#999"),
            ),
            secondary_y=False,
        )

    fig.add_trace(
        go.Scatter(
            x=price_df["date"],
            y=price_df["value"],
            name="Price",
            mode="lines",
            line=dict(width=1.5, color="red", dash="dot"),
        ),
        secondary_y=True,
    )

    fig.update_layout(
        template=TEMPLATE,
        title=english_title(
            "NEM Real-time Generation Mix & Price — Full Window (5-min)"
        ),
        yaxis_title="Power (MW)",
        hovermode="x unified",
        legend_title="Fuel group",
        margin=dict(b=110),
        height=600,
    )
    fig.update_yaxes(title_text="Power (MW)", secondary_y=False)
    last_date = price_df["date"].max()
    first_date = price_df["date"].min()
    
    fig.update_yaxes(title_text="Price (AUD/MWh)", secondary_y=True)
    fig.update_xaxes(
        tickformat="%m-%d %H:%M",
        range=[(last_date - pd.Timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'), last_date.strftime('%Y-%m-%d %H:%M:%S')],
        rangeslider=dict(
            visible=True,
            range=[first_date.strftime('%Y-%m-%d %H:%M:%S'), last_date.strftime('%Y-%m-%d %H:%M:%S')]
        ),
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1d", step="day", stepmode="backward"),
                dict(count=3, label="3d", step="day", stepmode="backward"),
                dict(count=7, label="1w", step="day", stepmode="backward"),
                dict(step="all", label="All")
            ])
        )
    )
    add_source_footer(fig, "Generation-only (battery charging & pumps excluded)")
    save(fig, "fig1_nem_realtime_mix.html")


# --------------------------------------------------------------------------- #
# Fig 2 — Monthly generation by fuel (available history)
# --------------------------------------------------------------------------- #
def fig2_annual() -> None:
    df = pd.read_csv(RAW_DIR / "nem_annual_fuel_mix.csv", parse_dates=["interval"])
    df = df[df["fueltech_group"] != "battery"]
    df["fueltech_group"] = df["fueltech_group"].replace("battery_discharging", "battery")
    df = df[df["fueltech_group"].isin(GEN_GROUPS)].copy()
    df["value"] = df["value"].clip(lower=0)
    groups = order_groups(sorted(df["fueltech_group"].unique()))
    dmin, dmax = df["interval"].min(), df["interval"].max()

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
        title=english_title(
            "NEM-Wide Monthly Generation by Fuel Type (All Regions)"
        ),
        yaxis_title="Energy (MWh)",
        xaxis_title="",
        hovermode="x unified",
        legend_title="Fuel group",
        margin=dict(b=120),
    )
    fig.update_xaxes(tickformat="%Y-%m")
    add_source_footer(
        fig,
        f"COMMUNITY plan: data limited to {dmin:%Y-%m}–{dmax:%Y-%m} (not full 2020–2025)",
    )
    save(fig, "fig2_annual_generation_by_fuel.html")


# --------------------------------------------------------------------------- #
# Fig 3 — Cross-state generation mix (latest 12 months)
# --------------------------------------------------------------------------- #
def fig3_state_comparison() -> None:
    df = pd.read_csv(RAW_DIR / "nem_state_fuel_mix.csv")
    df = df[df["fueltech_group"] != "battery"]
    df["fueltech_group"] = df["fueltech_group"].replace("battery_discharging", "battery")
    df = df[df["fueltech_group"].isin(GEN_GROUPS) & df["network_region"].notna()].copy()
    df["value"] = df["value"].clip(lower=0)
    # Sum over the full 12-month window per region × group.
    agg = df.groupby(["network_region", "fueltech_group"])["value"].sum().reset_index()
    groups = order_groups(sorted(agg["fueltech_group"].unique()))

    fig = go.Figure()
    regions = [r for r in REGION_ORDER if r in agg["network_region"].unique()]
    ylabels = [REGION_LABELS.get(r, r) for r in regions]
    for g in groups:
        vals = [
            agg[(agg["network_region"] == r) & (agg["fueltech_group"] == g)]["value"].sum()
            for r in regions
        ]
        fig.add_trace(
            go.Bar(
                y=ylabels,
                x=vals,
                name=g,
                orientation="h",
                marker_color=FUEL_COLORS.get(g, "#999"),
            )
        )
    fig.update_layout(
        template=TEMPLATE,
        barmode="stack",
        title=english_title(
            "Generation Mix by State — Latest 12 Months"
        ),
        xaxis_title="Energy (MWh)",
        yaxis_title="",
        legend_title="Fuel group",
        margin=dict(b=110),
    )
    add_source_footer(fig, "Sum of monthly energy over the latest 12 months")
    save(fig, "fig3_state_comparison.html")


# --------------------------------------------------------------------------- #
# Fig 4 — Coal retirement timeline (Gantt)
# --------------------------------------------------------------------------- #
def fig4_coal_timeline() -> None:
    df = pd.read_csv(RAW_DIR / "nem_coal_facilities.csv").copy()
    df["commenced"] = pd.to_datetime(df["commenced"], utc=True).dt.tz_localize(None)
    df["retired"] = pd.to_datetime(df["retired"], utc=True).dt.tz_localize(None)
    df = df.dropna(subset=["commenced", "retired"])
    df["label"] = df["facility_name"] + " · " + df["unit_code"].astype(str)
    df["region"] = df["network_region"].map(REGION_LABELS).fillna(df["network_region"])
    df = df.sort_values("retired")

    fig = px.timeline(
        df,
        x_start="commenced",
        x_end="retired",
        y="label",
        color="status",
        color_discrete_map={"operating": "#5dade2", "retired": "#c0392b"},
        hover_data={"region": True, "capacity_mw": True, "fueltech": True},
    )
    fig.update_yaxes(autorange="reversed", title="", dtick=1)
    fig.update_layout(
        template=TEMPLATE,
        title=english_title(
            "NEM Coal Unit Operating & Retirement Timeline"
        ),
        xaxis_title="",
        legend_title="Status",
        height=max(500, 25 * len(df)),
        margin=dict(t=50, b=110, l=250),
    )
    fig.update_xaxes(tickformat="%Y")
    add_source_footer(fig, "End date for operating units = expected closure date")
    save(fig, "fig4_coal_retirement_timeline.html")


def main() -> int:
    print("Generating charts -> outputs/figures/")
    fig1_realtime()
    fig2_annual()
    fig3_state_comparison()
    fig4_coal_timeline()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
