"""Unified Streamlit dashboard for HDRE NEM research figures."""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    from .config import CHAPTERS
    from .styles import inject_styles
except ImportError:
    from config import CHAPTERS
    from styles import inject_styles


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
UPDATED_DATE = datetime(2026, 6, 22)

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
def load_realtime_generation() -> pd.DataFrame:
    df = pd.read_parquet(RAW_DIR / "nem_realtime_7d.parquet")
    df = df[df["fueltech_group"].isin(GEN_GROUPS)].copy()
    df["value"] = df["value"].clip(lower=0)
    df["interval"] = pd.to_datetime(df["interval"])
    return df


def ordered_groups(groups: list[str]) -> list[str]:
    return [group for group in STACK_ORDER if group in groups]


def build_energy_terrain(df: pd.DataFrame) -> go.Figure:
    groups = ordered_groups(sorted(df["fueltech_group"].unique()))
    pivot = (
        df.groupby(["interval", "fueltech_group"], observed=True)["value"]
        .sum()
        .unstack(fill_value=0)
        .sort_index()
    )
    pivot = pivot.reindex(columns=groups, fill_value=0)

    intervals = list(pivot.index)
    start = intervals[0]
    x_hours = np.array([(interval - start).total_seconds() / 3600 for interval in intervals])

    fig = go.Figure()
    for index, group in enumerate(groups):
        values = pivot[group].to_numpy(dtype=float)
        x_grid = np.vstack([x_hours, x_hours])
        y_grid = np.vstack([
            np.full_like(x_hours, index - 0.34, dtype=float),
            np.full_like(x_hours, index + 0.34, dtype=float),
        ])
        z_grid = np.vstack([values, values])
        fig.add_trace(
            go.Surface(
                x=x_grid,
                y=y_grid,
                z=z_grid,
                name=FUEL_LABELS[group],
                showscale=False,
                opacity=0.92,
                surfacecolor=np.full_like(z_grid, index, dtype=float),
                colorscale=[[0, FUEL_COLORS[group]], [1, FUEL_COLORS[group]]],
                hovertemplate=(
                    f"{FUEL_LABELS[group]}<br>"
                    "Hour %{x:.1f}<br>"
                    "Power %{z:,.0f} MW<extra></extra>"
                ),
            )
        )

    totals = pivot.sum(axis=1)
    solar_peak_time = pivot["solar"].idxmax() if "solar" in pivot else totals.idxmax()
    solar_peak = float(pivot.loc[solar_peak_time, "solar"]) if "solar" in pivot else 0.0
    coal_avg = float(pivot["coal"].mean()) if "coal" in pivot else 0.0
    wind_std_time = pivot["wind"].sub(pivot["wind"].mean()).abs().idxmax() if "wind" in pivot else totals.idxmax()
    evening_window = pivot[(pivot.index.hour >= 17) & (pivot.index.hour <= 21)]
    evening_peak_time = evening_window.sum(axis=1).idxmax() if not evening_window.empty else totals.idxmax()

    callouts = [
        ("Solar peak", solar_peak_time, "solar", solar_peak),
        ("Coal baseload", pivot.index[len(pivot) // 2], "coal", coal_avg),
        ("Evening ramp", evening_peak_time, "gas" if "gas" in groups else groups[0], float(totals.loc[evening_peak_time])),
        ("Wind variation", wind_std_time, "wind" if "wind" in groups else groups[-1], float(pivot.loc[wind_std_time].max())),
    ]
    for label, when, group, z_value in callouts:
        if group not in groups:
            continue
        fig.add_trace(
            go.Scatter3d(
                x=[(when - start).total_seconds() / 3600],
                y=[groups.index(group)],
                z=[z_value],
                mode="markers+text",
                text=[label],
                textposition="top center",
                marker=dict(size=4, color=FUEL_COLORS.get(group, "#D8D2C0"), line=dict(width=1, color="#F5EEDC")),
                textfont=dict(size=11, color="#EFE8D2"),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    tick_positions = np.linspace(float(x_hours.min()), float(x_hours.max()), 5)
    tick_text = [
        (start + pd.Timedelta(hours=float(hour))).strftime("%d %b %H:%M")
        for hour in tick_positions
    ]

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=620,
        margin=dict(l=0, r=0, t=22, b=0),
        scene=dict(
            bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                title="Time",
                tickmode="array",
                tickvals=tick_positions,
                ticktext=tick_text,
                gridcolor="rgba(239,232,210,0.10)",
                zerolinecolor="rgba(239,232,210,0.12)",
                color="#B9B2A3",
            ),
            yaxis=dict(
                title="Fuel layer",
                tickmode="array",
                tickvals=list(range(len(groups))),
                ticktext=[FUEL_LABELS[group] for group in groups],
                gridcolor="rgba(239,232,210,0.08)",
                zerolinecolor="rgba(239,232,210,0.10)",
                color="#B9B2A3",
            ),
            zaxis=dict(
                title="Power (MW)",
                gridcolor="rgba(239,232,210,0.10)",
                zerolinecolor="rgba(239,232,210,0.12)",
                color="#B9B2A3",
            ),
            camera=dict(eye=dict(x=1.55, y=-1.85, z=1.18)),
            aspectratio=dict(x=2.0, y=0.9, z=0.72),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(color="#D8D2C0", size=11),
        ),
    )
    return fig


def realtime_metrics(df: pd.DataFrame) -> list[dict[str, str]]:
    totals = df.groupby("fueltech_group")["value"].sum()
    total = float(totals.sum())
    renewable = float(totals.reindex(list(RENEWABLE_GROUPS), fill_value=0).sum())
    solar_peak = float(df[df["fueltech_group"] == "solar"]["value"].max())
    wind_share = float(totals.get("wind", 0) / total * 100)
    coal_share = float(totals.get("coal", 0) / total * 100)
    return [
        {"label": "Coal baseload", "value": f"{coal_share:.1f}", "unit": "%", "note": "Share of seven-day generation"},
        {"label": "Solar peak", "value": f"{solar_peak / 1000:.1f}", "unit": "GW", "note": "Highest observed interval"},
        {"label": "Wind contribution", "value": f"{wind_share:.1f}", "unit": "%", "note": "Energy share across window"},
        {"label": "Renewable share", "value": f"{renewable / total * 100:.1f}", "unit": "%", "note": "Solar, wind, hydro, bioenergy"},
        {"label": "Data points", "value": f"{len(df):,}", "unit": "rows", "note": "30-minute fuel-group records"},
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
    st.markdown(
        f"""
        <div class="topbar">
            <div>
                <div class="terminal-label">HDRE NEM research terminal</div>
                <div class="terminal-meta">OpenElectricity source · Updated {UPDATED_DATE:%d %b %Y} · Chapter {escape(chapter["id"])}</div>
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

        st.markdown(
            """
            <div class="sidebar-footer">
                <div class="sidebar-footer-label">operational scope</div>
                <div class="sidebar-footer-row"><span>NEM regions</span><span>5</span></div>
                <div class="sidebar-footer-row"><span>Published figures</span><span>5</span></div>
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
    df = load_realtime_generation()
    fig = build_energy_terrain(df)

    title_col, download_col = st.columns([5, 1.2], vertical_alignment="top")
    with title_col:
        st.markdown(
            f"""
            <div class="figure-kicker">Chapter 1.2 · Figure 01 · live grid layer</div>
            <h1 class="main-title">{escape(figure["title"])}</h1>
            <div class="main-subtitle">{escape(figure["subtitle"])} · 3D fuel-layer terrain from 30-minute MW intervals</div>
            """,
            unsafe_allow_html=True,
        )
    with download_col:
        render_downloads(figure)

    st.markdown('<div class="chart-module hero-module">', unsafe_allow_html=True)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "responsive": True})
    st.markdown("</div>", unsafe_allow_html=True)

    render_metric_tiles(realtime_metrics(df))
    st.markdown(
        """
        <div class="research-note">
            <div class="note-label">research note</div>
            <div>Coal remains the structural baseload layer, while solar creates the strongest intraday shape. Midday renewable surplus is followed by a visible evening ramp.</div>
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
        st.iframe(html_path.read_text(encoding="utf-8"), height=560)
    else:
        missing = escape(str(html_path.relative_to(PROJECT_ROOT) if html_path else "No HTML path configured"))
        st.markdown(f'<div class="missing-file">Missing chart file: {missing}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    render_standard_metrics(figure.get("metrics", []))
    st.markdown(
        f"""
        <div class="research-note">
            <div class="note-label">key takeaway</div>
            <div>{escape(figure.get("takeaway", ""))}</div>
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
