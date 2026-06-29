"""Unified Streamlit dashboard for HDRE NEM research figures."""

from __future__ import annotations

from datetime import datetime
from html import escape
import json
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
        "button_label": "Update This Analysis",
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
        "button_label": "Update This Analysis",
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
        "button_label": "Update This Analysis",
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
        "button_label": "Update This Analysis",
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
        "button_label": "Refresh Market Signals",
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


def ch3_global_comparison_html(html: str) -> str:
    """Apply the Chapter 3 Figure 02 display-only Plotly redesign."""
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
            "Australia": "#00c9a7"
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
            ["Australia (APAC growth leader)", "#00c9a7"]
        ];

        function redesign() {
            const graph = document.querySelector(".plotly-graph-div");
            if (!graph || !window.Plotly || !graph.data || !graph.data.length) {
                window.setTimeout(redesign, 80);
                return;
            }

            const barTrace = Object.assign({}, graph.data[0]);
            const countries = barTrace.y || [];
            const growthPoints = countries.map((country) => ({
                country: country,
                growthRate: growthRates[country]
            }));
            barTrace.marker = Object.assign({}, barTrace.marker, {
                color: countries.map((country) => regionColors[country] || "rgba(255,255,255,0.15)")
            });
            barTrace.showlegend = false;

            const growthTrace = {
                type: "scatter",
                mode: "markers",
                x: growthPoints.map((point) => point.growthRate),
                y: growthPoints.map((point) => point.country),
                xaxis: "x2",
                yaxis: "y",
                name: "Growth rate (%/yr)",
                hovertemplate: "<b>%{y}</b><br>Growth rate: %{x:.1f}%/yr<extra></extra>",
                marker: {
                    symbol: "diamond",
                    size: 9,
                    color: countries.map((country) => country === "Australia" ? "#00c9a7" : "rgba(255,255,255,0.5)"),
                    line: { color: "rgba(5,12,10,0.85)", width: 1 }
                },
                showlegend: false
            };

            const legendTraces = legendItems.map(([name, color]) => ({
                type: "scatter",
                mode: "markers",
                x: [null],
                y: [null],
                name: name,
                marker: { color: color, size: 10, symbol: "square" },
                hoverinfo: "skip",
                showlegend: true
            }));

            const layout = Object.assign({}, graph.layout, {
                bargap: 0.5,
                showlegend: true,
                legend: Object.assign({}, graph.layout.legend, {
                    orientation: "h",
                    x: 0,
                    y: 1.18,
                    xanchor: "left",
                    yanchor: "bottom"
                }),
                xaxis2: {
                    title: { text: "Growth rate (%/yr)", font: { color: "#B8BDB9", size: 12 } },
                    overlaying: "x",
                    side: "top",
                    range: [5, 32],
                    tickfont: { color: "#6B7570", size: 11 },
                    gridcolor: "rgba(255,255,255,0.04)",
                    zeroline: false,
                    showline: true,
                    linecolor: "rgba(255,255,255,0.12)"
                }
            });

            if (layout.annotations && layout.annotations.length) {
                layout.annotations = layout.annotations.map((annotation) => (
                    annotation.y === "Australia"
                        ? Object.assign({}, annotation, {
                            x: growthRates["Australia"],
                            xref: "x2",
                            y: "Australia",
                            yref: "y",
                            arrowcolor: "#00c9a7",
                            font: Object.assign({}, annotation.font, { color: "#00c9a7" })
                        })
                        : annotation
                ));
            }

            Plotly.react(graph, [barTrace, growthTrace].concat(legendTraces), layout, {
                displayModeBar: false,
                responsive: true
            });
        }

        redesign();
    }());
    </script>
    """
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
    </script>
    """
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
        div[data-testid="stHorizontalBlock"]:has(.analysis-refresh-status) button {
            border-color: rgba(0, 201, 167, 0.34) !important;
            color: #D9FFF7 !important;
            background: rgba(0, 201, 167, 0.08) !important;
            min-height: 32px !important;
            padding: 4px 12px !important;
            box-shadow: none !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.analysis-refresh-status) button:hover {
            border-color: rgba(0, 201, 167, 0.62) !important;
            background: rgba(0, 201, 167, 0.13) !important;
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
        if st.button(config["button_label"], use_container_width=False):
            with st.spinner(f"Updating {config['scope_label']}..."):
                ok, message = run_registered_refresh(config)
            if ok:
                st.cache_data.clear()
                st.success(message)
                st.rerun()
            else:
                st.error(f"Refresh failed: {message}")

    with log_col:
        with st.popover("Run Details", use_container_width=False):
            log_path = config["log_path"]
            if log_path.exists():
                st.code(log_path.read_text(encoding="utf-8"), language="text")
            else:
                st.caption("No refresh log available yet.")


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


def render_standard_figure(entry: dict[str, Any]) -> None:
    figure = entry["figure"]
    chapter = entry["chapter"]

    if figure.get("type") == "outline":
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
