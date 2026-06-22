"""Chapter 1.1 Step 2 — Generate the 6 QLD drill-down charts (HTML + PNG).

Narrative follows the data: QLD's renewable buildout started slow (2020-21) then
accelerated sharply in 2024-25, converging with NSW at ~32% renewable share, with
a battery-heavy committed pipeline. The original "stagnation vs NSW surge" thesis
is NOT supported by the data and is not asserted.

Reuses the Chapter 1.2 fuel color map and styling.
Run: python scripts/04_generate_qld_charts.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
FIG_DIR = PROJECT_ROOT / "outputs" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Consistent with Chapter 1.2 (scripts/02_generate_charts.py)
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
REGION_LABELS = {"NSW1": "NSW", "QLD1": "QLD", "VIC1": "VIC", "SA1": "SA", "TAS1": "TAS"}
STATE_COLORS = {"QLD": "#c0392b", "NSW": "#2980b9", "VIC": "#27ae60", "SA": "#f39c12", "TAS": "#8e44ad"}
GEN_GROUPS = ["coal", "gas", "hydro", "wind", "solar", "bioenergy", "distillate", "battery"]
STACK_ORDER = ["coal", "gas", "distillate", "hydro", "wind", "solar", "bioenergy", "battery"]
SOURCE_FOOTER = "Source: OpenElectricity API (openelectricity.org.au)"
TEMPLATE = "plotly_white"


def bilingual_title(en: str, zh: str) -> str:
    return f"{en}<br><sub style='color:#666'>{zh}</sub>"


def add_source_footer(fig: go.Figure, extra: str = "") -> None:
    text = SOURCE_FOOTER + (f"　|　{extra}" if extra else "")
    fig.add_annotation(
        text=text, xref="paper", yref="paper", x=0, y=-0.16,
        showarrow=False, font=dict(size=10, color="#888"), align="left",
    )


def save(fig: go.Figure, name: str) -> None:
    html = FIG_DIR / f"{name}.html"
    fig.write_html(html, include_plotlyjs="cdn")
    msg = f"  wrote {name}.html ({html.stat().st_size/1024:.0f} KB)"
    try:
        png = FIG_DIR / f"{name}.png"
        fig.write_image(png, width=1100, height=650, scale=2)
        msg += f" + PNG ({png.stat().st_size/1024:.0f} KB)"
    except Exception as exc:  # noqa: BLE001
        msg += f" [PNG skipped: {type(exc).__name__}]"
    print(msg)


def order_groups(present) -> list[str]:
    return [g for g in STACK_ORDER if g in present]


# --------------------------------------------------------------------------- #
# Fig 1 — QLD renewable share vs peers (last 24 months)
# --------------------------------------------------------------------------- #
def fig1_renewable_vs_peers() -> None:
    df = pd.read_parquet(RAW_DIR / "nem_renewable_share.parquet")
    df = df[df["network_region"].notna()]
    piv = (
        df.pivot_table(index=["network_region", "interval"], columns="renewable",
                       values="value", aggfunc="sum")
        .rename(columns={True: "ren", False: "non"}).reset_index()
    )
    piv["share"] = piv["ren"] / (piv["ren"] + piv["non"]) * 100

    fig = go.Figure()
    for r in ["NSW1", "VIC1", "SA1", "TAS1", "QLD1"]:
        sub = piv[piv["network_region"] == r].sort_values("interval")
        if sub.empty:
            continue
        label = REGION_LABELS[r]
        is_qld = r == "QLD1"
        fig.add_trace(go.Scatter(
            x=sub["interval"], y=sub["share"], name=label, mode="lines+markers",
            line=dict(width=4 if is_qld else 1.8, color=STATE_COLORS[label]),
            opacity=1.0 if is_qld else 0.55,
        ))
    # Honest annotation: QLD converged with NSW (no fabricated "NSW surge").
    qn = piv[piv["network_region"].isin(["QLD1", "NSW1"])].sort_values("interval")
    # Use an ISO string (tz-aware Timestamps are not JSON-serializable for PNG export).
    last = pd.Timestamp(qn["interval"].max()).tz_localize(None).isoformat()
    fig.add_annotation(
        x=last, y=33, text="QLD has converged with NSW (~32%)<br>QLD 已追平 NSW（約 32%）",
        showarrow=True, arrowhead=2, ax=-90, ay=-50, font=dict(size=11, color="#c0392b"),
    )
    fig.update_layout(
        template=TEMPLATE,
        title=bilingual_title("QLD Renewable Share vs Peer States (Last 24 Months)",
                              "昆士蘭再生能源佔比與其他州比較（最近 24 個月）"),
        yaxis_title="Renewable share (%)", xaxis_title="", hovermode="x unified",
        legend_title="State", margin=dict(b=120),
    )
    fig.update_xaxes(tickformat="%Y-%m")
    fig.update_yaxes(range=[0, 100])
    add_source_footer(fig, "Window limited to ~24 months by COMMUNITY plan")
    save(fig, "qld_fig1_renewable_vs_peers")


# --------------------------------------------------------------------------- #
# Fig 2 — QLD fuel mix evolution (stacked area, 24 months)
# --------------------------------------------------------------------------- #
def fig2_fuel_mix() -> None:
    df = pd.read_parquet(RAW_DIR / "qld_fuel_mix_24m.parquet")
    df = df[df["fueltech_group"].isin(GEN_GROUPS)].copy()
    df["value"] = df["value"].clip(lower=0)
    groups = order_groups(sorted(df["fueltech_group"].unique()))
    fig = go.Figure()
    for g in groups:
        sub = df[df["fueltech_group"] == g].sort_values("interval")
        fig.add_trace(go.Scatter(
            x=sub["interval"], y=sub["value"], name=g, mode="lines", stackgroup="one",
            line=dict(width=0.5, color=FUEL_COLORS.get(g, "#999")),
            fillcolor=FUEL_COLORS.get(g, "#999"),
        ))
    fig.update_layout(
        template=TEMPLATE,
        title=bilingual_title("QLD Monthly Generation by Fuel Type (Last 24 Months)",
                              "昆士蘭各燃料類型每月發電量（最近 24 個月）"),
        yaxis_title="Energy (MWh)", xaxis_title="", hovermode="x unified",
        legend_title="Fuel group", margin=dict(b=120),
    )
    fig.update_xaxes(tickformat="%Y-%m")
    add_source_footer(fig, "Generation-only (battery charging & pumps excluded)")
    save(fig, "qld_fig2_fuel_mix_evolution")


# --------------------------------------------------------------------------- #
# Fig 3 — QLD utility solar vs wind cumulative capacity
# --------------------------------------------------------------------------- #
def fig3_solar_vs_wind() -> None:
    ch = pd.read_parquet(RAW_DIR / "qld_capacity_history.parquet")
    ch = ch[ch["month"] >= pd.Timestamp(2010, 1, 1)]
    fig = go.Figure()
    for ft, label, color in [("solar_utility", "Utility solar 大型太陽能", FUEL_COLORS["solar"]),
                             ("wind", "Wind 風電", FUEL_COLORS["wind"])]:
        sub = ch[ch["fueltech"] == ft].sort_values("month")
        fig.add_trace(go.Scatter(
            x=sub["month"], y=sub["capacity_mw"], name=label, mode="lines",
            line=dict(width=3, color=color),
        ))
    fig.update_layout(
        template=TEMPLATE,
        title=bilingual_title("QLD Utility Solar vs Wind — Cumulative Installed Capacity",
                              "昆士蘭大型太陽能與風電 — 累計裝置容量"),
        yaxis_title="Installed capacity (MW)", xaxis_title="", hovermode="x unified",
        legend_title="Technology", margin=dict(b=110),
    )
    fig.update_xaxes(tickformat="%Y")
    add_source_footer(fig, "Derived from facility commissioning/closure dates")
    save(fig, "qld_fig3_solar_vs_wind_buildout")


# --------------------------------------------------------------------------- #
# Fig 4 — YoY renewable capacity additions: QLD vs NSW vs VIC (grouped bar)
# --------------------------------------------------------------------------- #
def fig4_capacity_growth() -> None:
    pa = pd.read_parquet(RAW_DIR / "peer_capacity_additions.parquet")
    pa = pa[(pa["year"] >= 2020) & (pa["year"] <= 2026)].copy()
    pa["state"] = pa["network_region"].map(REGION_LABELS)
    years = list(range(2020, 2027))
    fig = go.Figure()
    for r in ["QLD1", "NSW1", "VIC1"]:
        label = REGION_LABELS[r]
        vals = [pa[(pa["network_region"] == r) & (pa["year"] == y)]["mw_added"].sum() for y in years]
        fig.add_trace(go.Bar(
            x=years, y=vals, name=label, marker_color=STATE_COLORS[label],
            opacity=1.0 if r == "QLD1" else 0.7,
        ))
    fig.update_layout(
        template=TEMPLATE, barmode="group",
        title=bilingual_title("Renewable Capacity Added per Year — QLD vs NSW vs VIC",
                              "每年新增再生能源容量 — 昆士蘭 vs 新南威爾斯 vs 維多利亞"),
        yaxis_title="MW added (commissioned that year)", xaxis_title="Year",
        legend_title="State", margin=dict(b=110),
    )
    add_source_footer(fig, "Solar/wind/hydro/bioenergy; from facility commissioning dates. 2026 = partial year")
    save(fig, "qld_fig4_capacity_growth_rate")


# --------------------------------------------------------------------------- #
# Fig 5 — QLD coal plants still operating (horizontal bar)
# --------------------------------------------------------------------------- #
def fig5_coal_operating() -> None:
    fac = pd.read_parquet(RAW_DIR / "qld_facilities.parquet")
    coal = fac[(fac["fueltech"] == "coal_black") & (fac["status_id"] == "operating")].copy()
    # Aggregate to plant level (sum unit capacity, earliest closure date).
    grp = coal.groupby("name").agg(
        capacity_mw=("capacity_registered", "sum"),
        closure=("closure_date", "min"),
    ).reset_index()
    grp["retire_year"] = grp["closure"].dt.year
    grp["retire_label"] = grp["retire_year"].apply(lambda y: str(int(y)) if pd.notna(y) else "TBD")
    grp = grp.sort_values("retire_year", na_position="last")
    total_mw = grp["capacity_mw"].sum()

    fig = go.Figure(go.Bar(
        x=grp["capacity_mw"], y=grp["name"], orientation="h",
        marker_color=FUEL_COLORS["coal"],
        text=[f"{c:.0f} MW · ~{r}" for c, r in zip(grp["capacity_mw"], grp["retire_label"])],
        textposition="outside",
    ))
    fig.update_layout(
        template=TEMPLATE,
        title=bilingual_title("QLD Coal Plants Still Operating — Capacity & Expected Retirement",
                              "昆士蘭仍運轉的燃煤電廠 — 容量與預期除役年"),
        xaxis_title="Operating capacity (MW)", yaxis_title="",
        margin=dict(b=110, l=160), height=max(450, 40 * len(grp)),
    )
    fig.add_annotation(
        x=1, y=1.02, xref="paper", yref="paper", showarrow=False, align="right",
        text=f"Total operating black coal: {total_mw:,.0f} MW　|　運轉中燃煤總計 {total_mw:,.0f} MW",
        font=dict(size=12, color="#c0392b"),
    )
    add_source_footer(fig, "Retirement years are expected closures (AEMO-sourced); TBD = not disclosed")
    save(fig, "qld_fig5_coal_still_operating")


# --------------------------------------------------------------------------- #
# Fig 6 — QLD negative spot-price frequency (saturation signal)
# --------------------------------------------------------------------------- #
def fig6_negative_prices() -> None:
    sp = pd.read_parquet(RAW_DIR / "qld_spot_prices.parquet")
    sp["interval"] = pd.to_datetime(sp["interval"])
    sp["month"] = sp["interval"].dt.tz_localize(None).dt.to_period("M").dt.to_timestamp()
    sp["neg"] = sp["price"] < 0
    monthly = sp.groupby("month").agg(neg_hours=("neg", "sum"), total=("neg", "count")).reset_index()
    monthly["pct"] = monthly["neg_hours"] / monthly["total"] * 100

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly["month"], y=monthly["neg_hours"], name="Negative-price hours 負電價時數",
        marker_color="#c0392b",
        text=[f"{h:.0f}h" for h in monthly["neg_hours"]], textposition="outside",
    ))
    fig.update_layout(
        template=TEMPLATE,
        title=bilingual_title("QLD1 Negative Spot-Price Hours per Month",
                              "昆士蘭 QLD1 每月負電價時數"),
        yaxis_title="Hours with price < $0/MWh", xaxis_title="", margin=dict(b=120),
    )
    fig.update_xaxes(tickformat="%Y-%m")
    add_source_footer(fig, "Hourly QLD1 spot price; negative prices signal midday solar oversupply")
    save(fig, "qld_fig6_curtailment_or_negative_price")


def main() -> int:
    print("Generating QLD charts -> outputs/figures/")
    fig1_renewable_vs_peers()
    fig2_fuel_mix()
    fig3_solar_vs_wind()
    fig4_capacity_growth()
    fig5_coal_operating()
    fig6_negative_prices()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
