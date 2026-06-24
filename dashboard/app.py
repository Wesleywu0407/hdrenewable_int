"""Unified Streamlit dashboard for HDRE NEM research figures."""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

try:
    from .config import CHAPTERS
    from .styles import inject_styles
except ImportError:
    from config import CHAPTERS
    from styles import inject_styles


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def get_last_updated() -> datetime:
    """Return the most recent modification time of any raw data file."""
    raw_dir = PROJECT_ROOT / "data" / "raw"
    if not raw_dir.exists():
        return datetime.now()
    data_files = list(raw_dir.glob("*.csv"))
    if not data_files:
        return datetime.now()
    return datetime.fromtimestamp(max(f.stat().st_mtime for f in data_files))


UPDATED_DATE = get_last_updated()

GEN_GROUPS = ["coal", "gas", "hydro", "wind", "solar", "bioenergy", "distillate", "battery"]
STACK_ORDER = ["coal", "gas", "distillate", "hydro", "wind", "solar", "bioenergy", "battery"]
RENEWABLE_GROUPS = {"solar", "wind", "hydro", "bioenergy"}
FUEL_COLORS = {
    "coal": "#3B3D3F",
    "gas": "#C46A2B",
    "solar": "#D6A21D",
    "wind": "#66B7C8",
    "hydro": "#557C9D",
    "battery": "#5D9C58",
    "bioenergy": "#8E7E45",
    "distillate": "#8A4A25",
}
FUEL_LABELS = {
    "coal": "Coal",
    "gas": "Gas",
    "distillate": "Distillate",
    "hydro": "Hydro",
    "wind": "Wind",
    "solar": "Solar",
    "bioenergy": "Bioenergy",
    "battery": "Battery",
}


def project_path(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def figure_key(chapter: dict[str, Any], figure: dict[str, Any]) -> str:
    return f"{chapter['id']}::{figure['id']}"


def all_figures() -> list[dict[str, Any]]:
    figures: list[dict[str, Any]] = []
    for chapter in CHAPTERS:
        for figure in chapter.get("figures", []):
            if figure.get("status", "published") != "unpublished":
                figures.append({"key": figure_key(chapter, figure), "chapter": chapter, "figure": figure})
    return figures


def selected_entry(figures: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not figures:
        return None
    valid_keys = {entry["key"] for entry in figures}
    if st.session_state.get("selected_figure") not in valid_keys:
        st.session_state.selected_figure = figures[0]["key"]
    return next(entry for entry in figures if entry["key"] == st.session_state.selected_figure)


@st.cache_data(show_spinner=False)
def load_realtime_generation(updated_timestamp: float = 0.0) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(RAW_DIR / "master_NEM_open_electricity.csv", parse_dates=["date"])
    
    # Use all data in the CSV

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

    price_df = (
        df[["date", "Price - AUD/MWh"]]
        .dropna(subset=["Price - AUD/MWh"])
        .rename(columns={"Price - AUD/MWh": "value", "date": "interval"})
        .sort_values("interval")
    )
    price_df["interval"] = pd.to_datetime(price_df["interval"])

    mw_cols = [c for c in WIDE_TO_FUEL if c in df.columns]
    melted = pd.melt(
        df, id_vars=["date"], value_vars=mw_cols,
        var_name="fueltech_group", value_name="value",
    )
    melted["fueltech_group"] = melted["fueltech_group"].map(WIDE_TO_FUEL)
    melted["value"] = melted["value"].clip(lower=0)
    melted = melted.rename(columns={"date": "interval"})
    melted["interval"] = pd.to_datetime(melted["interval"])
    
    melted = melted.groupby(["interval", "fueltech_group"], as_index=False)["value"].sum()
    melted = melted[melted["fueltech_group"].isin(GEN_GROUPS)].copy()
    
    return melted, price_df


def ordered_groups(groups: list[str]) -> list[str]:
    return [group for group in STACK_ORDER if group in groups]


def build_realtime_mix_chart(df: pd.DataFrame, price_df: pd.DataFrame) -> go.Figure:
    groups = ordered_groups(sorted(df["fueltech_group"].unique()))
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for group in groups:
        sub = df[df["fueltech_group"] == group].sort_values("interval")
        fig.add_trace(
            go.Scatter(
                x=sub["interval"],
                y=sub["value"],
                name=FUEL_LABELS[group],
                mode="lines",
                stackgroup="generation",
                line=dict(width=0.8, color=FUEL_COLORS[group]),
                fillcolor=FUEL_COLORS[group],
                opacity=0.92,
                hovertemplate=(
                    f"{FUEL_LABELS[group]}<br>"
                    "%{x|%d %b %H:%M}<br>"
                    "Power %{y:,.0f} MW<extra></extra>"
                ),
            ),
            secondary_y=False,
        )

    fig.add_trace(
        go.Scatter(
            x=price_df["interval"],
            y=price_df["value"],
            name="Price",
            mode="lines",
            line=dict(width=1.5, color="#E74C3C", dash="dot"),
            hovertemplate="Price<br>%{x|%d %b %H:%M}<br>$%{y:,.2f}/MWh<extra></extra>",
        ),
        secondary_y=True,
    )

    if not df.empty:
        max_date = df["interval"].max()
        min_date = max_date - pd.Timedelta(days=7)
        range_opts = dict(range=[min_date, max_date])
    else:
        range_opts = {}

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=560,
        margin=dict(l=10, r=10, t=35, b=34),
        xaxis=dict(
            title="",
            tickformat="%d %b<br>%H:%M",
            gridcolor="rgba(239,232,210,0.08)",
            zerolinecolor="rgba(239,232,210,0.12)",
            color="#B9B2A3",
            showspikes=True,
            spikemode="across",
            spikecolor="rgba(239,232,210,0.22)",
            **range_opts,
            rangeselector=dict(
                x=1,
                y=1.12,
                xanchor="right",
                yanchor="bottom",
                buttons=list([
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(count=14, label="2w", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(step="all", label="all")
                ]),
                bgcolor="rgba(0,0,0,0.5)",
                activecolor="rgba(255,255,255,0.2)",
            )
        ),
        yaxis=dict(
            title="Power (MW)",
            gridcolor="rgba(239,232,210,0.08)",
            zerolinecolor="rgba(239,232,210,0.12)",
            color="#B9B2A3",
            rangemode="tozero",
        ),
        yaxis2=dict(
            title="Price (AUD/MWh)",
            gridcolor="rgba(0,0,0,0)",
            color="#E74C3C",
            overlaying="y",
            side="right",
            rangemode="tozero",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(color="#D8D2C0", size=11),
        ),
        hovermode="x unified",
    )
    return fig


def realtime_metrics(df: pd.DataFrame) -> list[dict[str, str]]:
    totals = df.groupby("fueltech_group")["value"].sum()
    total = float(totals.sum())
    # Guard against division by zero when dataframe is empty or all-NaN
    safe_total = total or 1
    renewable = float(totals.reindex(list(RENEWABLE_GROUPS), fill_value=0).sum())
    solar_peak = float(df[df["fueltech_group"] == "solar"]["value"].max()) if not df.empty else 0.0
    wind_share = float(totals.get("wind", 0) / safe_total * 100)
    coal_share = float(totals.get("coal", 0) / safe_total * 100)
    return [
        {"label": "Coal baseload", "value": f"{coal_share:.1f}", "unit": "%", "note": "Share of generation in window"},
        {"label": "Solar peak", "value": f"{solar_peak / 1000:.1f}", "unit": "GW", "note": "Highest observed interval"},
        {"label": "Wind contribution", "value": f"{wind_share:.1f}", "unit": "%", "note": "Energy share across window"},
        {"label": "Renewable share", "value": f"{renewable / safe_total * 100:.1f}", "unit": "%", "note": "Solar, wind, hydro, bioenergy"},
        {"label": "Data points", "value": f"{len(df):,}", "unit": "rows", "note": "5-minute fuel-group records"},
    ]


def render_downloads(figure: dict[str, Any]) -> None:
    png_path = project_path(figure.get("png_path"))
    html_path = project_path(figure.get("html_path"))
    cols = st.columns(2, gap="small")
    with cols[0]:
        if png_path and png_path.exists():
            st.download_button("PNG", png_path.read_bytes(), png_path.name, "image/png", width="stretch")
        else:
            st.button("PNG", disabled=True, width="stretch")
    with cols[1]:
        if html_path and html_path.exists():
            st.download_button("HTML", html_path.read_bytes(), html_path.name, "text/html", width="stretch")
        else:
            st.button("HTML", disabled=True, width="stretch")


def render_header(entry: dict[str, Any]) -> None:
    figure = entry["figure"]
    chapter = entry["chapter"]
    # Determine the source label: prefer figure-level, then chapter-level, then fallback
    source_label = figure.get("source") or chapter.get("source") or "AEMO / OpenElectricity"
    st.markdown(
        f"""
        <div class="topbar">
            <div>
                <div class="terminal-label">HDRE NEM research terminal</div>
                <div class="terminal-meta">{escape(source_label)} · Updated {UPDATED_DATE:%d %b %Y} · Chapter {escape(chapter["id"])}</div>
            </div>
            <div class="system-state">published artifact · fig {figure["number"]:02d}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(figures: list[dict[str, Any]]) -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-mark">HDRE</div>
                <div>
                    <div class="sidebar-title">FIELD INDEX</div>
                    <div class="sidebar-caption">Australia NEM research atlas</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if figures and "selected_figure" not in st.session_state:
            st.session_state.selected_figure = figures[0]["key"]

        for chapter in CHAPTERS:
            status = chapter.get("status", "planned")
            if status == "done" and chapter.get("figures"):
                st.markdown(
                    f'<div class="chapter-strip">Chapter {escape(chapter["id"])} · {escape(chapter["title"])}</div>',
                    unsafe_allow_html=True,
                )
                for figure in chapter["figures"]:
                    key = figure_key(chapter, figure)
                    fig_status = figure.get("status", "published")
                    if fig_status == "unpublished":
                        st.markdown(
                            f"""
                            <div class="artifact-card" style="opacity: 0.5;">
                                <div class="artifact-number">FIG {figure["number"]:02d}</div>
                                <div class="artifact-title">{escape(figure.get("sidebar_title", figure["title"]).upper())}</div>
                                <div class="artifact-status">status: unpublished</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        continue

                    label = f"FIG {figure['number']:02d}\n{figure.get('sidebar_title', figure['title']).upper()}\nstatus: published"
                    active = st.session_state.get("selected_figure") == key
                    if active:
                        st.markdown(
                            f"""
                            <div class="artifact-card active">
                                <div class="artifact-number">FIG {figure["number"]:02d}</div>
                                <div class="artifact-title">{escape(figure.get("sidebar_title", figure["title"]).upper())}</div>
                                <div class="artifact-status published">status: published</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    elif st.button(label, key=f"nav_{key}", width="stretch"):
                        st.session_state.selected_figure = key
                        st.rerun()
                continue

            status_label = "in progress" if status == "wip" else "planned"
            st.markdown(
                f"""
                <div class="roadmap-card">
                    <div class="artifact-number">{escape(chapter["id"])}</div>
                    <div class="artifact-title">{escape(chapter["title"]).upper()}</div>
                    <div class="artifact-status">{status_label}</div>
                    <div class="roadmap-subtitle">{escape(chapter.get("subtitle", ""))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        total_figures = sum(len(ch.get("figures", [])) for ch in CHAPTERS if ch.get("status") == "done")
        st.markdown(
            f"""
            <div class="sidebar-footer">
                <div class="sidebar-footer-label">operational scope</div>
                <div class="sidebar-footer-row"><span>NEM regions</span><span>5</span></div>
                <div class="sidebar-footer-row"><span>Published figures</span><span>{total_figures}</span></div>
                <div class="sidebar-footer-row"><span>Mode</span><span>research</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_metric_tiles(metrics: list[dict[str, str]]) -> None:
    columns = st.columns(len(metrics), gap="small")
    for col, metric in zip(columns, metrics):
        with col:
            st.markdown(
                f"""
                <div class="instrument-tile">
                    <div class="instrument-label">{escape(metric["label"])}</div>
                    <div class="instrument-value">{escape(metric["value"])}<span>{escape(metric.get("unit", ""))}</span></div>
                    <div class="instrument-note">{escape(metric.get("note", ""))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_standard_metrics(metrics: list[dict[str, str]]) -> None:
    columns = st.columns(max(1, min(3, len(metrics))), gap="small")
    for col, metric in zip(columns, metrics):
        with col:
            st.markdown(
                f"""
                <div class="instrument-tile compact">
                    <div class="instrument-label">{escape(metric["label"])}</div>
                    <div class="instrument-value">{escape(metric["value"])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_figure_one(entry: dict[str, Any]) -> None:
    figure = entry["figure"]
    df, price_df = load_realtime_generation(UPDATED_DATE.timestamp())
    fig = build_realtime_mix_chart(df, price_df)

    chapter = entry["chapter"]
    title_col, download_col = st.columns([5, 1.2], vertical_alignment="top")
    with title_col:
        st.markdown(
            f"""
            <div class="figure-kicker">Chapter {escape(chapter["id"])} · Figure {figure["number"]:02d} · live generation profile</div>
            <h1 class="main-title">{escape(figure["title"])}</h1>
            <div class="main-subtitle">{escape(figure["subtitle"])} · 2D stacked generation profile from 5-minute MW intervals</div>
            """,
            unsafe_allow_html=True,
        )
    with download_col:
        render_downloads(figure)

    st.markdown('<div class="chart-module hero-module">', unsafe_allow_html=True)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "responsive": True})
    st.markdown("</div>", unsafe_allow_html=True)

    render_metric_tiles(realtime_metrics(df))
    
    takeaway = figure.get("takeaway", "")
    description = figure.get("description", "")
    if takeaway or description:
        st.markdown(
            f"""
            <div class="research-note">
                {f'<div class="note-label">key takeaway</div><div>{escape(takeaway)}</div>' if takeaway else ''}
                {f'<div class="note-label" style="margin-top: 1rem;">graph description</div><div>{escape(description)}</div>' if description else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_standard_figure(entry: dict[str, Any]) -> None:
    figure = entry["figure"]
    chapter = entry["chapter"]
    html_path = project_path(figure.get("html_path"))

    title_col, download_col = st.columns([5, 1.2], vertical_alignment="top")
    with title_col:
        st.markdown(
            f"""
            <div class="figure-kicker">Chapter {escape(chapter["id"])} · Figure {figure["number"]:02d} · generated artifact</div>
            <h1 class="main-title">{escape(figure["title"])}</h1>
            <div class="main-subtitle">{escape(figure["subtitle"])}</div>
            """,
            unsafe_allow_html=True,
        )
    with download_col:
        render_downloads(figure)

    st.markdown('<div class="chart-module legacy-module">', unsafe_allow_html=True)
    if html_path and html_path.exists():
        st.iframe(html_path, height=560)
    else:
        missing = escape(str(html_path.relative_to(PROJECT_ROOT) if html_path else "No HTML path configured"))
        st.markdown(f'<div class="missing-file">Missing chart file: {missing}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    render_standard_metrics(figure.get("metrics", []))
    
    takeaway = figure.get("takeaway", "")
    description = figure.get("description", "")
    if takeaway or description:
        st.markdown(
            f"""
            <div class="research-note">
                {f'<div class="note-label">key takeaway</div><div>{escape(takeaway)}</div>' if takeaway else ''}
                {f'<div class="note-label" style="margin-top: 1rem;">graph description</div><div>{escape(description)}</div>' if description else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )


def main() -> None:
    st.set_page_config(
        page_title="HDRE · Australia NEM Research",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()

    figures = all_figures()
    render_sidebar(figures)
    entry = selected_entry(figures)
    if not entry:
        st.warning("No figures configured.")
        return

    render_header(entry)
    if entry["figure"]["id"] == "fig1":
        render_figure_one(entry)
    else:
        render_standard_figure(entry)


if __name__ == "__main__":
    main()
