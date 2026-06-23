"""Step 4 — Generate the 5 NEM analysis charts as standalone HTML.

Loads the 5 Parquet datasets from data/raw/ and writes interactive Plotly
charts to outputs/figures/. English titles, consistent fuel
colors, plotly_white template.

Run: python scripts/02_generate_charts.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
    df = pd.read_parquet(RAW_DIR / "nem_realtime_7d.parquet")
    df = df[df["fueltech_group"].isin(GEN_GROUPS)].copy()
    df["value"] = df["value"].clip(lower=0)  # generation-only stack
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
        title=english_title(
            "NEM Real-time Generation Mix — Past 7 Days (30-min)"
        ),
        yaxis_title="Power (MW)",
        xaxis_title="",
        hovermode="x unified",
        legend_title="Fuel group",
        margin=dict(b=110),
    )
    fig.update_xaxes(tickformat="%m-%d %H:%M")
    add_source_footer(fig, "Generation-only (battery charging & pumps excluded)")
    save(fig, "fig1_nem_realtime_mix.html")


# --------------------------------------------------------------------------- #
# Fig 2 — Monthly generation by fuel (available history)
# --------------------------------------------------------------------------- #
def fig2_annual() -> None:
    df = pd.read_parquet(RAW_DIR / "nem_annual_fuel_mix.parquet")
    df = df[df["fueltech_group"].isin(GEN_GROUPS)].copy()
    df["value"] = df["value"].clip(lower=0)
    groups = order_groups(sorted(df["fueltech_group"].unique()))
    dmin, dmax = df["interval"].min(), df["interval"].max()

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
        title=english_title(
            "NEM Monthly Generation by Fuel Type"
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
    df = pd.read_parquet(RAW_DIR / "nem_state_fuel_mix.parquet")
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
# Fig 4 — Renewable share evolution per state
# --------------------------------------------------------------------------- #
def fig4_renewable_share() -> None:
    df = pd.read_parquet(RAW_DIR / "nem_renewable_share.parquet")
    df = df[df["network_region"].notna()].copy()
    # Pivot renewable True/False to columns, compute share %.
    piv = (
        df.pivot_table(
            index=["network_region", "interval"],
            columns="renewable",
            values="value",
            aggfunc="sum",
        )
        .rename(columns={True: "renewable", False: "non_renewable"})
        .reset_index()
    )
    piv["share"] = piv["renewable"] / (piv["renewable"] + piv["non_renewable"]) * 100

    fig = go.Figure()
    for r in [x for x in REGION_ORDER if x in piv["network_region"].unique()]:
        sub = piv[piv["network_region"] == r].sort_values("interval")
        fig.add_trace(
            go.Scatter(
                x=sub["interval"],
                y=sub["share"],
                name=REGION_LABELS.get(r, r),
                mode="lines+markers",
            )
        )
    dmin, dmax = piv["interval"].min(), piv["interval"].max()
    fig.update_layout(
        template=TEMPLATE,
        title=english_title(
            "Renewable Energy Share by State"
        ),
        yaxis_title="Renewable share (%)",
        xaxis_title="",
        hovermode="x unified",
        legend_title="State",
        margin=dict(b=120),
    )
    fig.update_xaxes(tickformat="%Y-%m")
    fig.update_yaxes(range=[0, 100])
    add_source_footer(
        fig,
        f"COMMUNITY plan: data limited to {dmin:%Y-%m}–{dmax:%Y-%m} (not full 2020–2025)",
    )
    save(fig, "fig4_renewable_share_evolution.html")


# --------------------------------------------------------------------------- #
# Fig 5 — Coal retirement timeline (Gantt)
# --------------------------------------------------------------------------- #
def fig5_coal_timeline() -> None:
    df = pd.read_parquet(RAW_DIR / "nem_coal_facilities.parquet").copy()
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
    fig.update_yaxes(autorange="reversed", title="")
    fig.update_layout(
        template=TEMPLATE,
        title=english_title(
            "NEM Coal Unit Operating & Retirement Timeline"
        ),
        xaxis_title="",
        legend_title="Status",
        height=max(500, 18 * len(df)),
        margin=dict(b=110, l=180),
    )
    fig.update_xaxes(tickformat="%Y")
    add_source_footer(fig, "End date for operating units = expected closure date")
    save(fig, "fig5_coal_retirement_timeline.html")


def main() -> int:
    print("Generating charts -> outputs/figures/")
    fig1_realtime()
    fig2_annual()
    fig3_state_comparison()
    fig4_renewable_share()
    fig5_coal_timeline()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
