"""Unified Streamlit dashboard for HDRE NEM research figures."""

from __future__ import annotations

from datetime import datetime
from html import escape
import json
import sys
from pathlib import Path
import re
import subprocess
from typing import Any
from urllib.parse import quote

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
REFRESH_STATUS_DIR = PROJECT_ROOT / "runtime" / "refresh"
LOG_DIR = PROJECT_ROOT / "logs"
CH3_STATUS_PATH = PROJECT_ROOT / "runtime" / "ch3" / "last_run_status.json"
CH3_LOG_PATH = PROJECT_ROOT / "logs" / "ch3_refresh_log.txt"

REFRESH_REGISTRY = {
    "1.1::*": {
        "scope_label": "Queensland renewables",
        "button_label": "Update this analysis",
        "command": ["bash", "scripts/run_qld_scrape.sh"],
        "status_path": REFRESH_STATUS_DIR / "chapter_1_1_status.json",
        "log_path": LOG_DIR / "chapter_1_1_refresh.log",
        "expected_outputs": [
            "outputs/figures/fig1_1_qld_renewable_share.html",
            "outputs/figures/fig1_2_qld_fuel_mix.html",
            "outputs/figures/fig1_3_qld_negative_prices.html",
        ],
    },
    "1.3::fig1_4": {
        "scope_label": "Infrastructure & Storage Mapping",
        "button_label": "Update this analysis",
        "command": ["bash", "scripts/run_infrastructure_scrape.sh"],
        "status_path": REFRESH_STATUS_DIR / "chapter_1_3_status.json",
        "log_path": LOG_DIR / "chapter_1_3_refresh.log",
        "expected_outputs": [
            "data/raw/bess_locations.csv",
            "data/raw/datacentre_locations.csv",
            "outputs/figures/fig1_4_infrastructure_map.html",
        ],
    },
    "2.1::*": {
        "scope_label": "Electricity trading market",
        "button_label": "Update this analysis",
        "command": ["bash", "scripts/run_trading_scrape.sh"],
        "status_path": REFRESH_STATUS_DIR / "chapter_2_1_status.json",
        "log_path": LOG_DIR / "chapter_2_1_refresh.log",
        "expected_outputs": [
            "outputs/figures/fig2_1_spot_heatmap.html",
            "outputs/figures/fig2_2_fcas_regulation.html",
            "outputs/figures/fig2_3_fcas_contingency.html",
        ],
    },
    "2.2::fig2_4": {
        "scope_label": "Weather & Market Price Correlation",
        "button_label": "Update this analysis",
        "command": ["bash", "scripts/run_weather_scrape.sh"],
        "status_path": REFRESH_STATUS_DIR / "chapter_2_2_status.json",
        "log_path": LOG_DIR / "chapter_2_2_refresh.log",
        "expected_outputs": [
            "data/raw/weather_price_correlation.csv",
            "outputs/figures/fig2_4_weather_correlation.html",
        ],
    },
    "3::*": {
        "scope_label": "AI Data Center Power Demand",
        "button_label": "Refresh market signals",
        "command": ["python", "scripts/10_ch3_refresh_pipeline.py"],
        "status_path": CH3_STATUS_PATH,
        "log_path": CH3_LOG_PATH,
        "expected_outputs": [
            "runtime/ch3/latest_policy_news.json",
            "runtime/ch3/last_run_status.json",
            "logs/ch3_refresh_log.txt",
        ],
        "status_labels": {
            "success": "Signals Ready",
            "stale": "Signals Stale",
            "missing": "Not Refreshed Yet",
        },
        "time_label": "Last refreshed:",
    },
}

CARD_COLOR_PALETTE = {
    "fossil": "#8B6F47",
    "wind": "#1F8A5C",
    "solar": "#F5A623",
    "storage": "#5B8DEF",
    "market": "#6B5BD9",
}

CARD_CATEGORY_RULES = [
    ("coal", "fossil"),
    ("retired units", "fossil"),
    ("operating units", "fossil"),
    ("retiring by", "fossil"),
    ("gas", "fossil"),
    ("solar", "solar"),
    ("price volatility", "solar"),
    ("wind", "wind"),
    ("renewables", "wind"),
    ("renewable", "wind"),
    ("hydro", "wind"),
    ("bess", "storage"),
    ("battery", "storage"),
    ("fcas", "storage"),
    ("regulation", "storage"),
    ("contingency", "storage"),
    ("data centres", "market"),
    ("data centre", "market"),
    ("data window", "market"),
    ("weather points", "market"),
    ("spot price", "market"),
    ("price heatmap", "market"),
    ("comparison", "market"),
]

DEFAULT_CATEGORY = "market"


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


def render_downloads(figure: dict[str, Any]) -> None:
    png_path = project_path(figure.get("png_path"))
    html_path = project_path(figure.get("html_path"))
    cols = st.columns(2, gap="small")
    with cols[0]:
        if png_path and png_path.exists():
            st.download_button("PNG", png_path.read_bytes(), png_path.name, "image/png", use_container_width=True)
        else:
            st.button("PNG", disabled=True, use_container_width=True)
    with cols[1]:
        if html_path and html_path.exists():
            st.download_button("HTML", html_path.read_bytes(), html_path.name, "text/html", use_container_width=True)
        else:
            st.button("HTML", disabled=True, use_container_width=True)


def render_html(html: str) -> None:
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def ch3_global_comparison_html(html: str) -> str:
    """Apply the Chapter 3 Figure 02 display-only two-chart redesign."""
    overlay_script = """
    <script>
    (function () {
        const regionColors = {
            "United States": "#2a78d6",
            "Canada": "#2a78d6",
            "Germany": "#1baf7a",
            "United Kingdom": "#1baf7a",
            "Netherlands": "#1baf7a",
            "China": "#eda100",
            "Japan": "#eda100",
            "India": "#eda100",
            "Singapore": "#eda100",
            "Australia": "#199e70"
        };
        const growthRates = {
            "United States": 12.8,
            "China": 18.4,
            "Germany": 12.1,
            "United Kingdom": 14.3,
            "Canada": 11.9,
            "Netherlands": 15.7,
            "Japan": 13.2,
            "India": 22.4,
            "Australia": 25.1,
            "Singapore": 10.6
        };
        const legendItems = [
            ["North America", "#2a78d6"],
            ["Europe", "#1baf7a"],
            ["Asia-Pacific", "#eda100"],
            ["Australia - APAC growth leader", "#199e70"]
        ];

        function redesign() {
            const graph = document.querySelector(".plotly-graph-div");
            if (!graph || !window.Plotly || !graph.data || !graph.data.length) {
                window.setTimeout(redesign, 80);
                return;
            }

            const sourceTrace = graph.data[0] || {};
            const countries = sourceTrace.y || [];
            const capacities = sourceTrace.x || [];
            const rows = countries.map((country, index) => ({
                country: country,
                capacity: Number(capacities[index]),
                growth: growthRates[country],
                color: regionColors[country] || "rgba(255,255,255,0.16)"
            })).filter((row) => row.country && Number.isFinite(row.capacity));

            rows.sort((a, b) => b.capacity - a.capacity);
            const countryOrder = rows.map((row) => row.country);
            const colors = rows.map((row) => row.color);

            const capacityTrace = {
                type: "bar",
                orientation: "h",
                name: "Installed Capacity (GW)",
                x: rows.map((row) => row.capacity),
                y: countryOrder,
                marker: { color: colors, line: { color: "rgba(255,255,255,0.20)", width: 0.5 } },
                hovertemplate: "<b>%{y}</b><br>Installed capacity: %{x:.1f} GW<extra></extra>",
                showlegend: false,
                xaxis: "x",
                yaxis: "y"
            };

            const growthTrace = {
                type: "bar",
                orientation: "h",
                name: "Annual Growth Rate (%/yr)",
                x: rows.map((row) => row.growth),
                y: countryOrder,
                marker: { color: colors, line: { color: "rgba(255,255,255,0.20)", width: 0.5 } },
                hovertemplate: "<b>%{y}</b><br>Annual growth rate: %{x:.1f}%/yr<extra></extra>",
                showlegend: false,
                xaxis: "x2",
                yaxis: "y2"
            };

            const legendTraces = legendItems.map(([name, color]) => ({
                type: "scatter",
                mode: "markers",
                x: [null],
                y: [null],
                name: name,
                marker: { color: color, size: 9, symbol: "circle" },
                hoverinfo: "skip",
                showlegend: true
            }));

            const axisText = { color: "#B8BDB9", size: 11 };
            const tickText = { color: "#6B7570", size: 10 };
            const gridColor = "rgba(255,255,255,0.05)";
            const layout = Object.assign({}, graph.layout, {
                height: 860,
                bargap: 0.42,
                showlegend: true,
                legend: {
                    orientation: "h",
                    x: 0,
                    y: 1.04,
                    xanchor: "left",
                    yanchor: "bottom",
                    font: { color: "#B8BDB9", size: 12 },
                    itemwidth: 30
                },
                margin: { l: 125, r: 38, t: 82, b: 86 },
                plot_bgcolor: "rgba(0,0,0,0)",
                paper_bgcolor: "rgba(0,0,0,0)",
                hoverlabel: {
                    bgcolor: "#1e2433",
                    bordercolor: "#00c9a7",
                    font: { color: "#ffffff", size: 12 }
                },
                xaxis: {
                    domain: [0, 1],
                    anchor: "y",
                    title: { text: "Installed Capacity (GW)", font: axisText },
                    rangemode: "tozero",
                    gridcolor: gridColor,
                    zeroline: false,
                    showline: false,
                    tickfont: tickText
                },
                yaxis: {
                    domain: [0.66, 0.93],
                    anchor: "x",
                    categoryorder: "array",
                    categoryarray: countryOrder,
                    autorange: "reversed",
                    ticks: "",
                    showgrid: false,
                    zeroline: false,
                    showline: false,
                    tickfont: tickText
                },
                xaxis2: {
                    domain: [0, 1],
                    anchor: "y2",
                    title: { text: "Annual growth rate (%/yr)", font: axisText },
                    range: [0, 28],
                    gridcolor: gridColor,
                    zeroline: false,
                    showline: false,
                    tickfont: tickText
                },
                yaxis2: {
                    domain: [0.07, 0.47],
                    anchor: "x2",
                    categoryorder: "array",
                    categoryarray: countryOrder,
                    autorange: "reversed",
                    ticks: "",
                    showgrid: false,
                    zeroline: false,
                    showline: false,
                    tickfont: tickText
                },
                shapes: [
                    {
                        type: "line",
                        xref: "paper",
                        yref: "paper",
                        x0: 0,
                        x1: 1,
                        y0: 0.565,
                        y1: 0.565,
                        line: { color: "rgba(255,255,255,0.10)", width: 0.5 }
                    },
                    {
                        type: "rect",
                        xref: "paper",
                        yref: "paper",
                        x0: 0,
                        x1: 1,
                        y0: 0.55,
                        y1: 0.61,
                        fillcolor: "rgba(25,158,112,0.11)",
                        line: { color: "rgba(25,158,112,0.42)", width: 0.5 },
                        layer: "below"
                    }
                ],
                annotations: [
                    {
                        xref: "paper",
                        yref: "paper",
                        x: 0,
                        y: 0.965,
                        text: "Installed Capacity (GW)",
                        showarrow: false,
                        xanchor: "left",
                        font: { color: "#ffffff", size: 13 }
                    },
                    {
                        xref: "paper",
                        yref: "paper",
                        x: 0.018,
                        y: 0.58,
                        text: "Australia: fastest growth in APAC at 25.1%/yr - same installed base as India (1.3 GW), but accelerating fastest",
                        showarrow: false,
                        xanchor: "left",
                        font: { color: "#cfe9dd", size: 12 }
                    },
                    {
                        xref: "paper",
                        yref: "paper",
                        x: 0,
                        y: 0.505,
                        text: "Annual Growth Rate (%/yr)",
                        showarrow: false,
                        xanchor: "left",
                        font: { color: "#ffffff", size: 13 }
                    }
                ]
            });

            Plotly.react(graph, [capacityTrace, growthTrace].concat(legendTraces), layout, {
                displayModeBar: false,
                responsive: true
            });
        }

        redesign();
    }());
    </XXX>
    """.replace("XXX", "script")
    return html.replace("</body>", f"{overlay_script}</body>") if "</body>" in html else f"{html}{overlay_script}"


def ch3_renewable_gap_html(html: str) -> str:
    """Apply the Chapter 3 Figure 04 display-only Plotly redesign."""
    overlay_script = """
    <script>
    (function () {
        const years = [2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2040, 2045, 2050];
        const dcDemand = [4.0, 5.2, 6.5, 7.8, 9.0, 12.0, 13.5, 15.5, 18.0, 21.0, 24.0, 28.0, 31.0, 34.5];
        const renewSupply = [2.0, 2.3, 2.7, 3.1, 3.6, 4.2, 5.0, 5.9, 7.0, 8.4, 10.0, 14.5, 19.0, 22.5];
        const gaps = dcDemand.map((demand, index) => demand - renewSupply[index]);
        const gapPct = gaps.map((gap, index) => Math.round((gap / dcDemand[index]) * 100));
        const hoverData = years.map((year, index) => [
            dcDemand[index],
            renewSupply[index],
            gaps[index],
            gapPct[index]
        ]);

        function redesign() {
            const graph = document.querySelector(".plotly-graph-div");
            if (!graph || !window.Plotly) {
                window.setTimeout(redesign, 80);
                return;
            }

            const renewTrace = {
                type: "scatter",
                mode: "lines",
                name: "Available Renewable Supply",
                x: years,
                y: renewSupply,
                customdata: hoverData,
                line: { color: "#1baf7a", width: 2.5, shape: "spline" },
                marker: { color: "#1baf7a" },
                hovertemplate: "Renewable Supply: %{y:.1f} TWh<extra></extra>"
            };
            const gapTrace = {
                type: "scatter",
                mode: "lines",
                name: "HDRE Opportunity Zone",
                x: years,
                y: dcDemand,
                customdata: hoverData,
                fill: "tonexty",
                fillcolor: "rgba(227,73,72,0.12)",
                line: { color: "#e34948", width: 1.5, dash: "dot", shape: "spline" },
                hoverinfo: "skip"
            };
            const demandTrace = {
                type: "scatter",
                mode: "lines",
                name: "Total DC Demand",
                x: years,
                y: dcDemand,
                customdata: hoverData,
                fill: "tonexty",
                fillcolor: "rgba(227,73,72,0.12)",
                line: { color: "#e34948", width: 2.5, shape: "spline" },
                marker: { color: "#e34948" },
                hovertemplate: "DC Demand: %{y:.1f} TWh<br>Gap: %{customdata[2]:.1f} TWh (%{customdata[3]}% unmet)<extra></extra>"
            };

            const layout = Object.assign({}, graph.layout, {
                annotations: [
                    {
                        x: 2030,
                        y: 12,
                        text: "2030: 12 TWh<br>= 6% of NEM",
                        showarrow: true,
                        arrowhead: 2,
                        arrowcolor: "#e34948",
                        font: { color: "#e34948", size: 10 }
                    },
                    {
                        x: 2035,
                        y: 17,
                        text: "Gap: 55% unmet",
                        showarrow: true,
                        arrowhead: 2,
                        arrowcolor: "#e34948",
                        font: { color: "#e34948", size: 10 }
                    },
                    {
                        x: 2042,
                        y: 22,
                        text: "HDRE Opportunity Zone",
                        showarrow: false,
                        font: { color: "#e34948", size: 11 }
                    }
                ],
                xaxis: Object.assign({}, graph.layout.xaxis, {
                    range: [2025, 2050],
                    showgrid: false,
                    zeroline: false,
                    title: { text: "Year", font: { color: "#B8BDB9", size: 12 } },
                    tickfont: { color: "#6B7570", size: 11 },
                    linecolor: "rgba(255,255,255,0.12)"
                }),
                yaxis: Object.assign({}, graph.layout.yaxis, {
                    range: [0, 40],
                    title: { text: "Energy (TWh)", font: { color: "#B8BDB9", size: 12 } },
                    tickfont: { color: "#6B7570", size: 11 },
                    gridcolor: "rgba(255,255,255,0.06)",
                    zerolinecolor: "rgba(255,255,255,0.12)",
                    linecolor: "rgba(255,255,255,0.12)"
                }),
                legend: Object.assign({}, graph.layout.legend, {
                    orientation: "h",
                    yanchor: "bottom",
                    y: 1.02,
                    xanchor: "left",
                    x: 0
                }),
                height: 500,
                hovermode: "x unified"
            });

            Plotly.react(graph, [renewTrace, demandTrace, gapTrace], layout, {
                displayModeBar: false,
                responsive: true
            });
        }

        redesign();
    }());
    </XXX>
    """.replace("XXX", "script")
    return html.replace("</body>", f"{overlay_script}</body>") if "</body>" in html else f"{html}{overlay_script}"


def ch3_state_breakdown_html(html: str) -> str:
    """Render the Chapter 3 Figure 05 dashboard-only two-panel redesign."""
    states = ["NSW", "VIC", "QLD", "SA", "TAS"]
    pipeline = [11400, 9400, 800, 350, 50]
    renewable = [38, 45, 32, 80, 99]
    colors = ["#2a78d6", "#1baf7a", "#eda100", "#7f77dd", "#888780"]
    statuses = [
        "Largest pipeline · low green match",
        "Strong pipeline · growing renewables",
        "Low pipeline · early mover opportunity",
        "High renewables · small pipeline",
        "Near 100% renewables · minimal DC",
    ]
    states_sorted = ["TAS", "SA", "VIC", "NSW", "QLD"]
    renew_sorted = [99, 80, 45, 38, 32]
    colors_sorted = ["#888780", "#7f77dd", "#1baf7a", "#2a78d6", "#eda100"]

    fig = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.58, 0.42],
        horizontal_spacing=0.16,
        subplot_titles=("Planned pipeline by state", "Renewable share by state"),
    )
    fig.add_trace(
        go.Bar(
            x=states,
            y=pipeline,
            marker=dict(
                color=colors,
                line=dict(color="rgba(255,255,255,0.30)", width=1),
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Pipeline: %{y:,.0f} MW<br>"
                "Renewable: %{customdata[0]}%<br>"
                "%{customdata[1]}"
                "<extra></extra>"
            ),
            customdata=list(zip(renewable, statuses)),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=renew_sorted,
            y=states_sorted,
            orientation="h",
            marker=dict(
                color=colors_sorted,
                line=dict(color="rgba(255,255,255,0.30)", width=1),
            ),
            text=[f"{value}%" for value in renew_sorted],
            textposition="outside",
            textfont=dict(color="#ffffff", size=12),
            hovertemplate="<b>%{y}</b><br>Renewable share: %{x}%<extra></extra>",
            cliponaxis=False,
        ),
        row=1,
        col=2,
    )
    fig.update_layout(
        height=430,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#898781", family="Inter, system-ui, sans-serif", size=12),
        margin=dict(l=60, r=28, t=44, b=52),
        hovermode="closest",
        hoverlabel=dict(
            bgcolor="#1e2433",
            bordercolor="#00c9a7",
            font=dict(color="#ffffff", size=13),
        ),
    )
    fig.update_xaxes(
        title_text="NEM State",
        showgrid=False,
        zeroline=False,
        linecolor="rgba(255,255,255,0.12)",
        tickfont=dict(color="#898781"),
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title_text="Capacity (MW)",
        tickformat="~s",
        gridcolor="rgba(255,255,255,0.06)",
        zeroline=False,
        linecolor="rgba(255,255,255,0.12)",
        tickfont=dict(color="#898781"),
        row=1,
        col=1,
    )
    fig.update_xaxes(
        title_text="Renewable share (%)",
        range=[0, 110],
        showgrid=False,
        zeroline=False,
        linecolor="rgba(255,255,255,0.12)",
        tickfont=dict(color="#898781"),
        row=1,
        col=2,
    )
    fig.update_yaxes(
        autorange="reversed",
        gridcolor="rgba(255,255,255,0.06)",
        zeroline=False,
        linecolor="rgba(255,255,255,0.12)",
        tickfont=dict(color="#898781"),
        row=1,
        col=2,
    )
    fig.update_annotations(font=dict(color="#B8BDB9", size=12))
    return fig.to_html(include_plotlyjs="cdn", full_html=False, config={"displayModeBar": False, "responsive": True})


def figure_html(entry: dict[str, Any], html_path: Path) -> str:
    html = html_path.read_text(encoding="utf-8")
    chapter = entry["chapter"]
    figure = entry["figure"]
    if chapter.get("id") == "3" and figure.get("id") == "ch3_fig1":
        return ch3_global_comparison_html(html)
    if chapter.get("id") == "3" and figure.get("id") == "ch3_fig3":
        return ch3_renewable_gap_html(html)
    if chapter.get("id") == "3" and figure.get("id") == "ch3_fig4":
        return ch3_state_breakdown_html(html)
    return html


def metric_category(label: str) -> str:
    normalized_label = label.lower()
    for keyword, category in CARD_CATEGORY_RULES:
        if " " in keyword and keyword in normalized_label:
            return category
        if " " not in keyword and re.search(rf"\b{re.escape(keyword)}\b", normalized_label):
            return category
    print(f"[dashboard] KPI card category fallback: {label!r} -> {DEFAULT_CATEGORY}")
    return DEFAULT_CATEGORY


def render_header(entry: dict[str, Any]) -> None:
    figure = entry["figure"]
    chapter = entry["chapter"]
    # Determine the source label: prefer figure-level, then chapter-level, then fallback
    source_label = figure.get("source") or chapter.get("source") or "AEMO / OpenElectricity"
    system_state_html = ""
    if figure.get("type") != "outline":
        system_state_html = f'<div class="system-state">published artifact · fig {figure["number"]:02d}</div>'
    st.markdown(
        f"""
        <div class="topbar">
            <div>
                <div class="terminal-label">HDRE NEM research terminal</div>
                <div class="terminal-meta">{escape(source_label)} · Updated {UPDATED_DATE:%d %b %Y} · Chapter {escape(chapter["id"])}</div>
            </div>
            {system_state_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def refresh_config_for_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    exact_key = figure_key(entry["chapter"], entry["figure"])
    if exact_key in REFRESH_REGISTRY:
        return REFRESH_REGISTRY[exact_key]
    return REFRESH_REGISTRY.get(f"{entry['chapter'].get('id')}::*")


def read_refresh_status(config: dict[str, Any]) -> dict[str, Any] | None:
    status_path = config["status_path"]
    if not status_path.exists():
        return None
    try:
        return json.loads(status_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {
            "status": "failed",
            "last_updated": None,
            "last_error": "Unable to read refresh status.",
        }


def format_refresh_time(value: str | None) -> str:
    if not value:
        return "Not available"
    try:
        parsed = datetime.fromisoformat(value)
        local_time = parsed.astimezone()
    except ValueError:
        return value
    return local_time.strftime("%d %b %Y · %H:%M")


def parse_refresh_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def format_run_duration(start_time: datetime | None, end_time: datetime | None) -> str:
    if not start_time or not end_time:
        return "n/a"
    seconds = max(0, int((end_time - start_time).total_seconds()))
    if seconds < 60:
        return f"{seconds}s"
    minutes, remaining_seconds = divmod(seconds, 60)
    return f"{minutes}m {remaining_seconds}s"


def is_refresh_stale(value: str | None) -> bool:
    parsed_time = parse_refresh_datetime(value)
    if not parsed_time:
        return False
    now = datetime.now(parsed_time.tzinfo).astimezone(parsed_time.tzinfo) if parsed_time.tzinfo else datetime.now()
    return (now - parsed_time).total_seconds() > 24 * 60 * 60


def simplify_refresh_error(error_text: str) -> str:
    if "HTTP Error 403: Forbidden" in error_text:
        return "403 Forbidden"
    if "HTTP Error 404: Not Found" in error_text:
        return "404 Not Found"
    if "The read operation timed out" in error_text:
        return "Read timeout"
    if "Connection refused" in error_text:
        return "Connection refused"
    return error_text[:30]


def parse_refresh_log(raw_log: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {"sources": [], "files": []}
    current_list: str | None = None
    for raw_line in raw_log.splitlines():
        line = raw_line.strip()
        if not line:
            current_list = None
            continue
        if line.endswith(":"):
            current_list = line[:-1]
            continue
        if line.startswith("start_time:"):
            parsed["start_time"] = line.split(":", 1)[1].strip()
        elif line.startswith("end_time:"):
            parsed["end_time"] = line.split(":", 1)[1].strip()
        elif line.startswith("news_items_collected:"):
            parsed["items"] = line.split(":", 1)[1].strip()
        elif line.startswith("error:"):
            parsed["error"] = line.split(":", 1)[1].strip()
        elif line.startswith("status:"):
            parsed["status"] = line.split(":", 1)[1].strip()
        elif line.startswith("- ") and current_list == "sources_attempted":
            source_line = line[2:]
            source_name, _, detail = source_line.partition(": ")
            items_text, _, error_text = detail.partition(" | error: ")
            item_count = items_text.split(" ", 1)[0] if items_text else "0"
            parsed["sources"].append(
                {
                    "name": source_name,
                    "items": item_count,
                    "error": error_text.strip() or None,
                }
            )
        elif line.startswith("- ") and current_list in {"files_written", "expected_outputs"}:
            parsed["files"].append(line[2:])
    return parsed


def render_raw_refresh_log(raw_log: str, fallback_message: str = "No refresh log available yet.") -> None:
    if raw_log:
        with st.expander("View raw log", expanded=False):
            st.code(raw_log, language="text")
    else:
        st.caption(fallback_message)


def render_run_details(config: dict[str, Any], status: dict[str, Any] | None) -> None:
    log_path = config["log_path"]
    raw_log = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    if not status:
        st.caption("No run details available yet.")
        render_raw_refresh_log(raw_log)
        return

    parsed_log = parse_refresh_log(raw_log)
    start_time = parse_refresh_datetime(parsed_log.get("start_time"))
    end_time = parse_refresh_datetime(parsed_log.get("end_time") or status.get("last_updated"))
    duration = format_run_duration(start_time, end_time)
    header_time = end_time.astimezone().strftime("%d %b %Y · %H:%M") if end_time else "Not available"
    raw_status = status.get("status") or parsed_log.get("status")
    log_error = parsed_log.get("error")
    is_success = raw_status == "success" and log_error in {None, "none", ""}
    status_text = "Completed" if is_success else "Failed"
    status_color = "#5dcaa5" if is_success else "#ec6a5e"
    items = str(status.get("items_scraped", parsed_log.get("items", "0")))
    sources = parsed_log.get("sources", [])
    total_sources = len(sources)
    successful_sources = sum(1 for source in sources if not source.get("error"))
    sources_color = "#5dcaa5" if total_sources and successful_sources == total_sources else "#d4a857"
    files = status.get("files_updated") or parsed_log.get("files") or status.get("expected_outputs") or config.get("expected_outputs", [])

    render_html(
        f"""
        <style>
        .run-summary {{
            min-width: 360px;
        }}
        .run-summary-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding-bottom: 0.55rem;
            margin-bottom: 0.75rem;
        }}
        .run-summary-title {{
            color: var(--ivory);
            font-size: 13px;
            font-weight: 500;
        }}
        .run-summary-meta {{
            color: var(--muted);
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 11px;
            white-space: nowrap;
        }}
        .run-kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 8px;
            margin-bottom: 0.9rem;
        }}
        .run-kpi-card {{
            background: var(--surface-1);
            border: 0.5px solid rgba(255,255,255,0.08);
            border-radius: 6px;
            padding: 0.6rem 0.75rem;
        }}
        .run-kpi-label,
        .run-section-label {{
            color: var(--muted);
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }}
        .run-kpi-value {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 14px;
            margin-top: 0.3rem;
        }}
        .run-section-label {{
            margin: 0.85rem 0 0.45rem;
        }}
        .run-source-list {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .run-source-row {{
            display: grid;
            grid-template-columns: 10px minmax(0, 1fr) auto;
            align-items: center;
            gap: 8px;
            background: var(--surface-1);
            border: 0.5px solid rgba(255,255,255,0.06);
            border-radius: 6px;
            padding: 8px 10px;
        }}
        .run-dot {{
            width: 6px;
            height: 6px;
            border-radius: 999px;
            background: var(--dot);
        }}
        .run-source-name {{
            color: var(--ivory);
            font-size: 12px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .run-source-status {{
            color: var(--status);
            font-size: 11px;
            text-align: right;
            white-space: nowrap;
        }}
        .run-file-path {{
            color: #898781;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 11px;
            line-height: 1.7;
        }}
        @media (max-width: 700px) {{
            .run-kpi-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
            .run-summary-header {{
                align-items: flex-start;
                flex-direction: column;
            }}
        }}
        </style>
        <div class="run-summary">
            <div class="run-summary-header">
                <div class="run-summary-title">Last run summary</div>
                <div class="run-summary-meta">{escape(header_time)} · {escape(duration)}</div>
            </div>
            <div class="run-kpi-grid">
                <div class="run-kpi-card">
                    <div class="run-kpi-label">Status</div>
                    <div class="run-kpi-value" style="color: {status_color};">{status_text}</div>
                </div>
                <div class="run-kpi-card">
                    <div class="run-kpi-label">Items</div>
                    <div class="run-kpi-value" style="color: var(--ivory);">{escape(items)}</div>
                </div>
                <div class="run-kpi-card">
                    <div class="run-kpi-label">Sources</div>
                    <div class="run-kpi-value" style="color: {sources_color};">{successful_sources} / {total_sources}</div>
                </div>
                <div class="run-kpi-card">
                    <div class="run-kpi-label">Duration</div>
                    <div class="run-kpi-value" style="color: var(--ivory);">{escape(duration)}</div>
                </div>
            </div>
        </div>
        """
    )

    if sources:
        source_rows = "\n".join(
            f"""
            <div class="run-source-row">
                <span class="run-dot" style="--dot: {'#ec6a5e' if source.get('error') else '#5dcaa5'};"></span>
                <span class="run-source-name">{escape(source['name'])}</span>
                <span class="run-source-status" style="--status: {'#ec6a5e' if source.get('error') else '#5dcaa5'};">{escape(simplify_refresh_error(source['error']) if source.get('error') else f"{source['items']} items")}</span>
            </div>
            """
            for source in sources
        )
        render_html(
            f"""
            <div class="run-section-label">SOURCES ATTEMPTED</div>
            <div class="run-source-list">{source_rows}</div>
            """
        )

    if files:
        file_rows = "\n".join(f'<div class="run-file-path">{escape(str(path))}</div>' for path in files)
        render_html(
            f"""
            <div class="run-section-label">FILES UPDATED</div>
            {file_rows}
            """
        )

    render_raw_refresh_log(raw_log)


def write_refresh_status(config: dict[str, Any], payload: dict[str, Any]) -> None:
    status_path = config["status_path"]
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_refresh_log(config: dict[str, Any], lines: list[str]) -> None:
    log_path = config["log_path"]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_registered_refresh(config: dict[str, Any]) -> tuple[bool, str]:
    start_time = datetime.now().astimezone().isoformat()
    result = subprocess.run(
        config["command"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    end_time = datetime.now().astimezone().isoformat()

    if config["status_path"] != CH3_STATUS_PATH:
        status_payload = {
            "status": "success" if result.returncode == 0 else "failed",
            "last_updated": end_time,
            "scope_label": config["scope_label"],
            "command": config["command"],
            "expected_outputs": config["expected_outputs"],
            "last_error": None if result.returncode == 0 else (result.stderr or result.stdout or "Refresh failed.").strip(),
        }
        write_refresh_status(config, status_payload)
        write_refresh_log(
            config,
            [
                f"scope: {config['scope_label']}",
                f"start_time: {start_time}",
                f"end_time: {end_time}",
                f"command: {' '.join(config['command'])}",
                f"status: {status_payload['status']}",
                "expected_outputs:",
                *(f"- {path}" for path in config["expected_outputs"]),
                "",
                "stdout:",
                result.stdout.strip() or "(empty)",
                "",
                "stderr:",
                result.stderr.strip() or "(empty)",
            ],
        )

    if result.returncode == 0:
        return True, "Analysis updated."
    return False, (result.stderr or result.stdout or "Refresh failed.").strip()


def render_refresh_control(entry: dict[str, Any]) -> None:
    config = refresh_config_for_entry(entry)
    if not config:
        return

    status = read_refresh_status(config)
    raw_status = status.get("status") if status else None
    labels = config.get("status_labels", {})
    if raw_status == "success":
        if is_refresh_stale(status.get("end_time") or status.get("last_updated")):
            pill_text = labels.get("stale", "Stale")
            pill_color = "#d4a857"
        else:
            pill_text = labels.get("success", "Ready")
            pill_color = "#00c9a7"
    elif raw_status == "failed":
        pill_text = "Refresh Failed"
        pill_color = "#e34948"
    else:
        pill_text = labels.get("missing", "Not Updated")
        pill_color = "#898781"

    time_label = config.get("time_label", "Last updated:")
    last_updated_text = format_refresh_time(status.get("last_updated") if status else None)

    st.markdown(
        """
        <style>
        div[data-testid="stHorizontalBlock"]:has(.analysis-refresh-status) {
            align-items: center;
            margin: 0 0 10px;
            padding: 6px 8px;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 6px;
            background: rgba(8,14,12,0.42);
            min-height: 0 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.analysis-refresh-status) [data-testid="stVerticalBlock"] {
            gap: 0 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.analysis-refresh-status) .refresh-primary-action button {
            background: rgba(0, 201, 167, 0.15) !important;
            border: 0.5px solid rgba(0, 201, 167, 0.5) !important;
            border-radius: 6px !important;
            color: #5dcaa5 !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            min-height: 34px !important;
            padding: 6px 14px !important;
            box-shadow: none !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.analysis-refresh-status) .refresh-primary-action button:hover {
            background: rgba(0, 201, 167, 0.22) !important;
            border-color: #00c9a7 !important;
            color: #5dcaa5 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.analysis-refresh-status) div[data-testid="column"]:nth-of-type(2) button {
            background: rgba(0, 201, 167, 0.15) !important;
            border: 0.5px solid rgba(0, 201, 167, 0.5) !important;
            border-radius: 6px !important;
            color: #5dcaa5 !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            min-height: 34px !important;
            padding: 6px 14px !important;
            box-shadow: none !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.analysis-refresh-status) div[data-testid="column"]:nth-of-type(2) button:hover {
            background: rgba(0, 201, 167, 0.22) !important;
            border-color: #00c9a7 !important;
            color: #5dcaa5 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.analysis-refresh-status) .refresh-secondary-action button {
            background: transparent !important;
            border: 0 !important;
            color: rgba(255, 255, 255, 0.55) !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            min-height: 34px !important;
            padding: 6px 8px !important;
            box-shadow: none !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.analysis-refresh-status) .refresh-secondary-action button:hover {
            background: rgba(255, 255, 255, 0.04) !important;
            color: rgba(255, 255, 255, 0.85) !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.analysis-refresh-status) .refresh-secondary-action button svg {
            opacity: 0.6 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.analysis-refresh-status) div[data-testid="column"]:nth-of-type(3) button {
            background: transparent !important;
            border: 0 !important;
            color: rgba(255, 255, 255, 0.55) !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            min-height: 34px !important;
            padding: 6px 8px !important;
            box-shadow: none !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.analysis-refresh-status) div[data-testid="column"]:nth-of-type(3) button:hover {
            background: rgba(255, 255, 255, 0.04) !important;
            color: rgba(255, 255, 255, 0.85) !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.analysis-refresh-status) div[data-testid="column"]:nth-of-type(3) button svg {
            opacity: 0.6 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    status_col, button_col, log_col = st.columns([0.62, 0.18, 0.20], gap="small")
    with status_col:
        st.markdown(
            f"""
            <div class="analysis-refresh-status" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap; min-height: 32px;">
                <span style="
                    color: {pill_color};
                    border: 1px solid color-mix(in srgb, {pill_color} 56%, transparent);
                    background: color-mix(in srgb, {pill_color} 10%, transparent);
                    border-radius: 999px;
                    padding: 4px 9px;
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 0.04em;
                    text-transform: uppercase;
                ">{pill_text}</span>
                <span style="color: #A7AEA9; font-size: 12px;">
                    <span style="color: #7E8782;">{escape(time_label)}</span> {escape(last_updated_text)}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with button_col:
        st.markdown('<div class="refresh-primary-action">', unsafe_allow_html=True)
        if "pyodide" not in sys.modules and st.button(config["button_label"], use_container_width=False):
            with st.spinner(f"Updating {config['scope_label']}..."):
                ok, message = run_registered_refresh(config)
            if ok:
                st.cache_data.clear()
                st.success(message)
                st.rerun()
            else:
                st.error(f"Refresh failed: {message}")
        st.markdown("</div>", unsafe_allow_html=True)

    with log_col:
        st.markdown('<div class="refresh-secondary-action">', unsafe_allow_html=True)
        if "pyodide" not in sys.modules:
            with st.popover("Run details", use_container_width=False):
                render_run_details(config, status)
        st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar(figures: list[dict[str, Any]]) -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="hdre-branding">
                <a href="/" target="_self" class="hdre-wordmark-link">
                    <div class="hdre-wordmark">HDRE</div>
                </a>
                <div class="hdre-divider"></div>
                <div class="hdre-label">FIELD INDEX</div>
                <div class="hdre-subtitle">Australia NEM research atlas</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if figures and "selected_figure" not in st.session_state:
            st.session_state.selected_figure = figures[0]["key"]
        requested_figure = st.query_params.get("figure")
        valid_figure_keys = {entry["key"] for entry in figures}
        if requested_figure in valid_figure_keys:
            st.session_state.selected_figure = requested_figure
        elif figures and not requested_figure:
            st.session_state.selected_figure = figures[0]["key"]

        for chapter in CHAPTERS:
            status = chapter.get("status", "planned")
            chapter_keys = {
                figure_key(chapter, figure)
                for figure in chapter.get("figures", [])
            }
            is_current_chapter = st.session_state.get("selected_figure") in chapter_keys
            chapter_label = f"Chapter {chapter['id']} · {chapter['title']}"

            with st.expander(chapter_label, expanded=is_current_chapter):
                if status == "done" and chapter.get("figures"):
                    for figure in chapter["figures"]:
                        key = figure_key(chapter, figure)
                        fig_status = figure.get("status", "published")
                        if fig_status == "unpublished":
                            st.markdown(
                                f"""
                                <div class="artifact-card" style="opacity: 0.5;">
                                    <div class="artifact-title"><span class="artifact-dot dot-planned"></span>{escape(figure.get("sidebar_title", figure["title"]).upper())}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                            continue

                        label = figure.get("sidebar_title", figure["title"]).upper()
                        active = st.session_state.get("selected_figure") == key
                        
                        def set_fig(k=key):
                            st.session_state.selected_figure = k
                            st.query_params["figure"] = k

                        st.button(
                            label,
                            key=f"sidebar_btn_{key}",
                            on_click=set_fig,
                            use_container_width=True,
                            type="primary" if active else "secondary"
                        )
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


def render_standard_metrics(metrics: list[dict[str, str]], entry: dict[str, Any] | None = None) -> None:
    if entry and entry["chapter"].get("id") == "3" and entry["figure"].get("id") == "ch3_fig4":
        state_cards = [
            ("NSW", "#2a78d6", "11,400 MW", "38% renewable", "Largest pipeline"),
            ("VIC", "#1baf7a", "9,400 MW", "45% renewable", "Growing renewables"),
            ("QLD", "#eda100", "800 MW", "32% renewable", "Early mover opp."),
            ("SA", "#7f77dd", "350 MW", "80% renewable", "High renewables"),
            ("TAS", "#888780", "50 MW", "99% renewable", "Near 100% green"),
        ]
        columns = st.columns(5, gap="small")
        st.markdown(
            """
            <style>
            .ch3-state-card {
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 6px;
                padding: 12px 12px 11px;
                min-height: 112px;
                transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
            }
            .ch3-state-card:hover {
                transform: translateY(-4px);
                border-color: var(--state-color);
                box-shadow: 0 10px 24px rgba(0,0,0,0.22);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        for col, (state, color, capacity, renewable_text, note) in zip(columns, state_cards):
            with col:
                st.markdown(
                    f"""
                    <div class="ch3-state-card" style="
                        --state-color: {color};
                        background: color-mix(in srgb, {color} 12%, rgba(8,14,12,0.72));
                    ">
                        <div style="color: {color}; font-size: 12px; font-weight: 700; letter-spacing: 0.04em;">{state}</div>
                        <div style="color: #F5F5F0; font-size: 19px; font-weight: 700; margin-top: 8px;">{capacity}</div>
                        <div style="color: #A7AEA9; font-size: 12px; margin-top: 5px;">{renewable_text}</div>
                        <div style="color: #7E8782; font-size: 11px; line-height: 1.3; margin-top: 8px;">{note}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        return
    columns = st.columns(max(1, min(3, len(metrics))), gap="small")
    for col, metric in zip(columns, metrics):
        category = metric_category(metric["label"])
        with col:
            st.markdown(
                f"""
                <div class="instrument-tile compact kpi-card kpi-card--{category}">
                    <div class="instrument-label">{escape(metric["label"])}</div>
                    <div class="instrument-value">{escape(metric["value"])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_ch3_research_outline() -> None:
    step_cards = [
        {
            "href": f"?figure={quote('3::ch3_fig1')}",
            "pair": "1",
            "color": "#5b8def",
            "eyebrow": "FIG 02 · Q1",
            "title": "Global comparison",
            "metric": "1.3 GW",
            "label": "AU capacity · 25.1%/yr",
        },
        {
            "href": f"?figure={quote('3::ch3_fig2')}",
            "pair": "2",
            "color": "#a78bfa",
            "eyebrow": "FIG 03 · Q2",
            "title": "Demand forecast",
            "metric": "12 TWh",
            "label": "2030 · 6% of NEM",
        },
        {
            "href": f"?figure={quote('3::ch3_fig3')}",
            "pair": "3",
            "color": "#ec6a5e",
            "eyebrow": "FIG 04 · Q3",
            "title": "Green energy gap",
            "metric": "55%",
            "label": "2035 supply deficit",
        },
        {
            "href": f"?figure={quote('3::ch3_fig4')}",
            "pair": "4",
            "color": "#d4a857",
            "eyebrow": "FIG 05 · Q4",
            "title": "State breakdown",
            "metric": "11.4 GW",
            "label": "NSW pipeline",
        },
    ]
    step_card_html = "\n".join(
        f"""
        <a class="ch3-flow-card ch3-pair-{card['pair']}" href="{card['href']}" target="_self" style="--accent: {card['color']};">
            <div class="ch3-card-eyebrow">{card['eyebrow']}</div>
            <div class="ch3-flow-title">{card['title']}</div>
            <div class="ch3-flow-metric" style="color: {card['color']};">{card['metric']}</div>
            <div class="ch3-flow-label">{card['label']}</div>
        </a>
        """
        for card in step_cards
    )

    render_html(
        f"""
        <style>
        .ch3-outline-wrap {{
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }}
        .ch3-outline-hero .main-title {{
            margin-bottom: 0.65rem !important;
        }}
        .ch3-outline-hero p {{
            color: var(--muted);
            font-size: 15px;
            line-height: 1.65;
            margin: 0;
            max-width: 980px;
        }}
        .ch3-thesis-card,
        .ch3-question-card,
        .ch3-flow-card,
        .ch3-source-bar {{
            background: var(--surface-1);
            border: 0.5px solid rgba(255, 255, 255, 0.08);
            box-shadow: none;
        }}
        .ch3-thesis-card {{
            border-left: 3px solid #d4a857;
            border-radius: 0 8px 8px 0;
            padding: 1rem 1.25rem;
        }}
        .ch3-section-label,
        .ch3-thesis-label {{
            color: #d4a857;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.11em;
            text-transform: uppercase;
            margin-bottom: 0.65rem;
        }}
        .ch3-thesis-body {{
            color: var(--ivory);
            font-size: 17px;
            line-height: 1.65;
            max-width: 1040px;
        }}
        .ch3-question-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 1rem;
        }}
        .ch3-question-card {{
            border-left: 3px solid var(--accent);
            border-radius: 10px;
            padding: 1rem 1.1rem;
        }}
        .ch3-question-title {{
            color: var(--ivory);
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.02em;
            margin-bottom: 0.55rem;
        }}
        .ch3-question-card p {{
            color: #A7AEA9;
            font-size: 14px;
            line-height: 1.55;
            margin: 0;
        }}
        .ch3-flow-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 1rem;
        }}
        .ch3-flow-card {{
            display: block;
            border-top: 3px solid var(--accent);
            border-radius: 10px;
            padding: 1rem;
            text-decoration: none !important;
            transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
        }}
        .ch3-flow-card:hover {{
            transform: translateY(-2px);
            border-color: var(--accent);
            background: rgba(255, 255, 255, 0.045);
        }}
        .ch3-outline-wrap:has(.ch3-pair-1:hover) .ch3-pair-1 {{
            border-color: #5b8def;
            transform: translateY(-1px);
            background: rgba(91, 141, 239, 0.06);
        }}
        .ch3-outline-wrap:has(.ch3-pair-2:hover) .ch3-pair-2 {{
            border-color: #a78bfa;
            transform: translateY(-1px);
            background: rgba(167, 139, 250, 0.06);
        }}
        .ch3-outline-wrap:has(.ch3-pair-3:hover) .ch3-pair-3 {{
            border-color: #ec6a5e;
            transform: translateY(-1px);
            background: rgba(236, 106, 94, 0.06);
        }}
        .ch3-outline-wrap:has(.ch3-pair-4:hover) .ch3-pair-4 {{
            border-color: #d4a857;
            transform: translateY(-1px);
            background: rgba(212, 168, 87, 0.06);
        }}
        .ch3-card-eyebrow {{
            color: var(--muted);
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.1em;
            margin-bottom: 0.7rem;
        }}
        .ch3-flow-title {{
            color: var(--ivory);
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 0.9rem;
        }}
        .ch3-flow-metric {{
            font-size: 28px;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 0.35rem;
        }}
        .ch3-flow-label {{
            color: #898781;
            font-size: 12px;
            line-height: 1.35;
        }}
        .ch3-source-bar {{
            display: flex;
            align-items: center;
            gap: 0.7rem;
            flex-wrap: wrap;
            border-radius: 8px;
            padding: 0.8rem 1rem;
        }}
        .ch3-source-label {{
            color: var(--muted);
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-right: 0.15rem;
        }}
        .ch3-source-pill {{
            background: rgba(255,255,255,0.04);
            border: 0.5px solid rgba(255,255,255,0.08);
            border-radius: 4px;
            color: #898781;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 11px;
            padding: 3px 8px;
        }}
        @media (max-width: 900px) {{
            .ch3-question-grid,
            .ch3-flow-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        </style>
        <div class="ch3-outline-wrap">
            <section class="ch3-outline-hero">
                <h1 class="main-title">Chapter 3 · Impact of AI data centre power demand on the power grid</h1>
                <p>Impact of AI Data Center Power Demand on the Grid - assessing whether and where HDRE should enter the Australian green energy market over the next 5-10 years.</p>
            </section>

            <section class="ch3-thesis-card">
                <div class="ch3-thesis-label">CENTRAL THESIS</div>
                <div class="ch3-thesis-body">AI data centre demand in Australia will grow from 4 TWh to 34.5 TWh by 2050, but renewable supply will lag - creating a structural green energy deficit that defines HDRE's primary market opportunity.</div>
            </section>

            <section>
                <div class="ch3-question-grid">
                    <div class="ch3-question-card ch3-pair-1" style="--accent: #5b8def;">
                        <div class="ch3-question-title">Q1 · Global context</div>
                        <p>How does Australia's data centre capacity compare globally, and where is growth concentrated?</p>
                    </div>
                    <div class="ch3-question-card ch3-pair-2" style="--accent: #a78bfa;">
                        <div class="ch3-question-title">Q2 · Demand trajectory</div>
                        <p>How fast will AI power demand grow, and what share of the NEM will it consume?</p>
                    </div>
                    <div class="ch3-question-card ch3-pair-3" style="--accent: #ec6a5e;">
                        <div class="ch3-question-title">Q3 · Supply gap</div>
                        <p>Can existing renewable supply meet projected AI load - and how big is the gap?</p>
                    </div>
                    <div class="ch3-question-card ch3-pair-4" style="--accent: #d4a857;">
                        <div class="ch3-question-title">Q4 · Market entry</div>
                        <p>Which NEM state offers the best entry point - pipeline scale or green-energy readiness?</p>
                    </div>
                </div>
            </section>

            <section>
                <div class="ch3-section-label">ANALYSIS FLOW · CLICK ANY STEP TO OPEN THE FIGURE</div>
                <div class="ch3-flow-grid">
                    {step_card_html}
                </div>
            </section>

            <section class="ch3-source-bar">
                <span class="ch3-source-label">SOURCES</span>
                <span class="ch3-source-pill">AEMO 2026 ISP</span>
                <span class="ch3-source-pill">Oxford Economics</span>
                <span class="ch3-source-pill">Climate Council</span>
                <span class="ch3-source-pill">IEA 2024</span>
                <span class="ch3-source-pill">Baxtel / DatacenterMap</span>
            </section>
        </div>
        """
    )


def render_standard_figure(entry: dict[str, Any]) -> None:
    figure = entry["figure"]
    chapter = entry["chapter"]

    if figure.get("type") == "outline":
        if chapter.get("id") == "3" and figure.get("sidebar_title") == "RESEARCH OUTLINE":
            render_ch3_research_outline()
            return
        st.markdown(
            f"""
            <h1 class="main-title" style="margin-bottom: 8px !important;">{escape(figure["title"])}</h1>
            <div class="main-subtitle" style="font-size: 16px !important; color: var(--muted) !important; margin-bottom: 24px !important;">{escape(figure["subtitle"])}</div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(figure.get("description", ""), unsafe_allow_html=True)
        return

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

    if figure.get("html_path"):
        st.markdown('<div class="chart-module legacy-module">', unsafe_allow_html=True)
        if html_path and html_path.exists():
            iframe_height = figure.get("height", 560)
            st.components.v1.html(
                figure_html(entry, html_path),
                height=iframe_height,
                scrolling=figure.get("scrolling", False),
            )
        else:
            missing = escape(str(html_path.relative_to(PROJECT_ROOT) if html_path else "No HTML path configured"))
            st.markdown(f'<div class="missing-file">Missing chart file: {missing}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    render_standard_metrics(figure.get("metrics", []), entry)
    
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
    render_refresh_control(entry)
    render_standard_figure(entry)


if __name__ == "__main__":
    main()
