"""Unified Streamlit dashboard for HDRE NEM research figures."""

from __future__ import annotations

from datetime import datetime
from html import escape
import importlib.util
import json
import sys
from pathlib import Path
import re
import subprocess
from typing import Any
from urllib.parse import quote

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

# Dynamically import the map builder script
spec = importlib.util.spec_from_file_location(
    "infrastructure_charts", 
    PROJECT_ROOT / "scripts" / "08_generate_infrastructure_charts.py"
)
infrastructure_charts = importlib.util.module_from_spec(spec)
sys.modules["infrastructure_charts"] = infrastructure_charts
spec.loader.exec_module(infrastructure_charts)

RAW_DIR = PROJECT_ROOT / "data" / "raw"
REFRESH_STATUS_DIR = PROJECT_ROOT / "runtime" / "refresh"
LOG_DIR = PROJECT_ROOT / "logs"

REFRESH_REGISTRY = {
    "1.2::*": {
        "scope_label": "National Electricity Market grid analysis",
        "button_label": "Refresh",
        "command": ["bash", "scripts/run_nem_scrape.sh"],
        "status_path": REFRESH_STATUS_DIR / "chapter_1_2_status.json",
        "log_path": LOG_DIR / "chapter_1_2_refresh.log",
        "expected_outputs": [
            "outputs/figures/fig1_nem_realtime_mix.html",
            "outputs/figures/fig2_annual_generation_by_fuel.html",
            "outputs/figures/fig3_state_comparison.html",
        ],
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
    ("coverage", "market"),
]

DEFAULT_CATEGORY = "market"


@st.cache_data
def load_infrastructure_data():
    bess_df = pd.read_csv(PROJECT_ROOT / "data" / "raw" / "bess_locations.csv")
    solar_df = pd.read_csv(PROJECT_ROOT / "data" / "raw" / "solar_locations.csv")
    dc_df = pd.read_csv(PROJECT_ROOT / "data" / "raw" / "datacentre_locations.csv")
    
    # Clean up state strings
    bess_df['state'] = bess_df['state'].str.strip().str.upper()
    solar_df['state'] = solar_df['state'].astype(str).str.strip().str.upper()
    dc_df['state'] = dc_df['state'].astype(str).str.strip().str.upper()
    
    # Infer missing states in DC data based on city
    dc_df.loc[dc_df['state'] == 'NAN', 'state'] = None
    dc_df.loc[dc_df['state'].isna() & dc_df['city'].str.contains('Sydney', case=False, na=False), 'state'] = 'NSW'
    dc_df.loc[dc_df['state'].isna() & dc_df['city'].str.contains('Melbourne', case=False, na=False), 'state'] = 'VIC'
    dc_df.loc[dc_df['state'].isna() & dc_df['city'].str.contains('Brisbane', case=False, na=False), 'state'] = 'QLD'
    dc_df.loc[dc_df['state'].isna() & dc_df['city'].str.contains('Adelaide', case=False, na=False), 'state'] = 'SA'
    dc_df.loc[dc_df['state'].isna() & dc_df['city'].str.contains('Perth', case=False, na=False), 'state'] = 'WA'
    
    return bess_df, solar_df, dc_df


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
            st.download_button("PNG", png_path.read_bytes(), png_path.name, "image/png", width="stretch")
        else:
            st.button("PNG", disabled=True, width="stretch")
    with cols[1]:
        if html_path and html_path.exists():
            st.download_button("HTML", html_path.read_bytes(), html_path.name, "text/html", width="stretch")
        else:
            st.button("HTML", disabled=True, width="stretch")


def render_html(html: str) -> None:
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)




def figure_html(entry: dict[str, Any], html_path: Path) -> str:
    html = html_path.read_text(encoding="utf-8")
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
        if "pyodide" not in sys.modules and st.button(config["button_label"], width="content"):
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
            with st.popover("Run details", width="content"):
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
                            width="stretch",
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


HIGHLIGHT_AMBER_RE = re.compile(
    r"-?\$[\d,]+(?:\.\d+)?(?:/MWh)?"
    r"|\b\d+(?:\.\d+)?%"
    r"|\b\d+(?:,\d{3})*(?:\.\d+)?\s?(?:GW|MW|MWh)\b"
    r"|\b\d+ of \d+\b"
    r"|\b\d{2}:\d{2}-\d{2}:\d{2}\b"
)
HIGHLIGHT_PURPLE_RE = re.compile(r"\bBESS\b|\bbattery storage\b|\barbitrage\b|\bfirming\b", re.IGNORECASE)
DATA_FOOTNOTE_ICON = (
    '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">'
    '<ellipse cx="12" cy="5" rx="9" ry="3"/>'
    '<path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>'
    '<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>'
)


def apply_note_highlights(escaped_text: str) -> str:
    """Color-only emphasis: at most 2 amber (data/price) + 1 purple (BESS/strategy) per paragraph."""
    highlighted_paragraphs = []
    for paragraph in escaped_text.split("\n\n"):
        counts = {"amber": 0, "purple": 0}

        def amber_repl(match: re.Match) -> str:
            if counts["amber"] >= 2:
                return match.group(0)
            counts["amber"] += 1
            return f'<span class="hl-amber">{match.group(0)}</span>'

        def purple_repl(match: re.Match) -> str:
            if counts["purple"] >= 1:
                return match.group(0)
            counts["purple"] += 1
            return f'<span class="hl-purple">{match.group(0)}</span>'

        paragraph = HIGHLIGHT_AMBER_RE.sub(amber_repl, paragraph)
        paragraph = HIGHLIGHT_PURPLE_RE.sub(purple_repl, paragraph)
        highlighted_paragraphs.append(paragraph)
    return "\n\n".join(highlighted_paragraphs)


def format_note_text(text: str, highlight: bool = False) -> str:
    if not text:
        return ""
    text = escape(text)
    if highlight:
        text = apply_note_highlights(text)
    # Block-level headers: ^**Header**$ or ^**Header:**$ (with optional whitespace)
    text = re.sub(r'(?m)^\s*\*\*(.*?):?\*\*\s*$', r'<div class="note-label">\1</div>', text)
    # Inline bold:
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    return text.replace('\n', '<br>')


def split_description(text: str) -> tuple[list[str], list[str], list[str]]:
    """Split a description into visible paragraphs, source/methodology paragraphs, and data footnotes."""
    visible: list[str] = []
    sources: list[str] = []
    footnotes: list[str] = []
    for paragraph in text.split("\n\n"):
        if not paragraph.strip():
            continue
        if "scripts/" in paragraph or re.search(r"(?m)^\s*\*\*[^*]*sources:\*\*\s*$", paragraph):
            sources.append(paragraph)
        elif paragraph.lstrip().startswith("Data is "):
            footnotes.append(paragraph)
        else:
            visible.append(paragraph)
    return visible, sources, footnotes


def render_standard_metrics(metrics: list[dict[str, str]], entry: dict[str, Any] | None = None) -> None:
    if not metrics:
        return
    if len(metrics) == 1:
        metric = metrics[0]
        category = metric_category(metric["label"])
        accent_class = "hl-purple" if category == "storage" else "hl-amber"
        st.markdown(
            f"""
            <div class="stat-single">
                <div class="zone-label">{escape(metric["label"])}</div>
                <div class="stat-single-value {accent_class}">{escape(metric["value"])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
    cols_per_row = max(1, min(3, len(metrics)))
    columns = st.columns(cols_per_row, gap="small")
    for i, metric in enumerate(metrics):
        category = metric_category(metric["label"])
        with columns[i % cols_per_row]:
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
            "title": "State Mismatch",
            "metric": "34 of 48",
            "label": "DCs in NSW/VIC",
        },
        {
            "href": f"?figure={quote('3::ch3_fig2')}",
            "pair": "2",
            "color": "#8f86e8",
            "eyebrow": "FIG 03 · Q2",
            "title": "Price Volatility",
            "metric": "16.2%",
            "label": "Negative Price Freq",
        },
        {
            "href": f"?figure={quote('3::ch3_fig3')}",
            "pair": "3",
            "color": "#ec6a5e",
            "eyebrow": "FIG 04 · Q3",
            "title": "The Duck Curve",
            "metric": "Extreme",
            "label": "Midday Irradiance",
        },
        {
            "href": f"?figure={quote('3::ch3_fig4')}",
            "pair": "4",
            "color": "#f5c063",
            "eyebrow": "FIG 05 · Q4",
            "title": "Value of Firming",
            "metric": "Massive",
            "label": "Arbitrage Savings",
        },
    ]
    step_card_html = "\n".join(
        f"""
        <a class="ch3-flow-card ch3-pair-{card['pair']}" href="{card['href']}" target="_self" style="--accent: {card['color']};">
            <div class="ch3-card-eyebrow">{card['eyebrow']}</div>
            <div class="ch3-flow-title">{card['title']}</div>
            <div class="ch3-flow-metric">{card['metric']}</div>
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
            gap: 40px;
        }}
        .ch3-outline-hero .main-title {{
            margin-bottom: 0.65rem !important;
        }}
        .ch3-outline-hero p {{
            color: var(--muted);
            font-size: 15px;
            line-height: 1.65;
            margin: 0;
            max-width: 72ch;
        }}
        .ch3-question-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0 48px;
            border-top: 0.5px solid var(--hairline);
        }}
        .ch3-question-card {{
            padding: 18px 0 20px;
            border-bottom: 0.5px solid var(--hairline);
        }}
        .ch3-question-title {{
            display: flex;
            align-items: center;
            gap: 9px;
            color: var(--ivory);
            font-size: 13px;
            font-weight: 500;
            letter-spacing: 0.02em;
            margin-bottom: 8px;
            transition: color 140ms ease;
        }}
        .ch3-question-title::before {{
            content: "";
            flex: 0 0 auto;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--accent);
            opacity: 0.85;
        }}
        .ch3-question-card p {{
            color: var(--desc-gray);
            font-size: 14px;
            line-height: 1.6;
            margin: 0;
            max-width: 56ch;
        }}
        .ch3-flow-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
        }}
        .ch3-flow-card {{
            display: block;
            padding: 16px 18px 18px;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.03);
            text-decoration: none !important;
            transition: background 140ms ease, transform 140ms ease;
        }}
        .ch3-flow-card:hover {{
            transform: translateY(-2px);
            background: rgba(255, 255, 255, 0.06);
        }}
        .ch3-outline-wrap:has(.ch3-pair-1:hover) .ch3-flow-card.ch3-pair-1,
        .ch3-outline-wrap:has(.ch3-pair-2:hover) .ch3-flow-card.ch3-pair-2,
        .ch3-outline-wrap:has(.ch3-pair-3:hover) .ch3-flow-card.ch3-pair-3,
        .ch3-outline-wrap:has(.ch3-pair-4:hover) .ch3-flow-card.ch3-pair-4 {{
            background: rgba(255, 255, 255, 0.06);
        }}
        .ch3-outline-wrap:has(.ch3-pair-1:hover) .ch3-question-card.ch3-pair-1 .ch3-question-title,
        .ch3-outline-wrap:has(.ch3-pair-2:hover) .ch3-question-card.ch3-pair-2 .ch3-question-title,
        .ch3-outline-wrap:has(.ch3-pair-3:hover) .ch3-question-card.ch3-pair-3 .ch3-question-title,
        .ch3-outline-wrap:has(.ch3-pair-4:hover) .ch3-question-card.ch3-pair-4 .ch3-question-title {{
            color: var(--accent);
        }}
        .ch3-card-eyebrow {{
            color: var(--label-gray);
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        .ch3-flow-title {{
            color: var(--ivory);
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 14px;
        }}
        .ch3-flow-metric {{
            font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
            font-feature-settings: 'tnum' on, 'lnum' on;
            font-size: 28px;
            font-weight: 500;
            letter-spacing: -0.01em;
            line-height: 1.15;
            margin-bottom: 6px;
            color: var(--accent);
        }}
        .ch3-flow-label {{
            color: var(--label-gray);
            font-size: 12px;
            line-height: 1.35;
        }}
        .ch3-source-bar {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
            padding-top: 18px;
            border-top: 0.5px solid var(--hairline);
        }}
        .ch3-source-label {{
            color: var(--label-gray);
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin-right: 6px;
        }}
        .ch3-source-pill {{
            background: transparent;
            border: 0.5px solid var(--hairline);
            border-radius: 999px;
            color: var(--label-gray);
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 11px;
            padding: 4px 12px;
        }}
        @media (max-width: 900px) {{
            .ch3-question-grid {{
                grid-template-columns: 1fr;
            }}
            .ch3-flow-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
        }}
        </style>
        <div class="ch3-outline-wrap">
            <section class="ch3-outline-hero">
                <h1 class="main-title">Chapter 3 · Impact of AI data centre power demand on the power grid</h1>
                <p>Impact of AI Data Center Power Demand on the Grid - assessing whether and where HDRE should enter the Australian green energy market over the next 5-10 years.</p>
            </section>

            <section class="ch3-thesis-zone">
                <div class="zone-label">CENTRAL THESIS</div>
                <div class="takeaway-body">Data centres are heavily clustered in Southern states (<span class="hl-amber">71%</span>), while over <span class="hl-amber">62%</span> of upcoming BESS and solar firming capacity is located in the North. This geographic mismatch, combined with predictable intraday spot price volatility (16.2% negative pricing events), defines a lucrative <span class="hl-purple">arbitrage and firming</span> opportunity for HDRE.</div>
            </section>

            <section>
                <div class="ch3-question-grid">
                    <div class="ch3-question-card ch3-pair-1" style="--accent: #5b8def;">
                        <div class="ch3-question-title">Q1 · State Mismatch</div>
                        <p>Where are data centres being built compared to where BESS and solar capacity is located?</p>
                    </div>
                    <div class="ch3-question-card ch3-pair-2" style="--accent: #8f86e8;">
                        <div class="ch3-question-title">Q2 · Price Volatility</div>
                        <p>How frequently do negative wholesale prices occur, and how severe are the evening peaks?</p>
                    </div>
                    <div class="ch3-question-card ch3-pair-3" style="--accent: #ec6a5e;">
                        <div class="ch3-question-title">Q3 · The Duck Curve</div>
                        <p>How does solar irradiance directly drive the intraday collapse of energy prices?</p>
                    </div>
                    <div class="ch3-question-card ch3-pair-4" style="--accent: #f5c063;">
                        <div class="ch3-question-title">Q4 · Market entry</div>
                        <p>Which NEM state offers the best entry point - pipeline scale or green-energy readiness?</p>
                    </div>
                </div>
            </section>

            <section>
                <div class="zone-label">ANALYSIS FLOW · CLICK ANY STEP TO OPEN THE FIGURE</div>
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

    if figure.get("html_path") and figure.get("id") != "fig1_4":
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

    if figure.get("id") == "fig1_4":
        @st.fragment
        def render_fig1_4_fragment():
            map_container = st.container()
            
            states = ["NSW", "QLD", "VIC", "SA", "TAS"]
            
            st.markdown('<div style="font-size: 16px; font-weight: 500; color: #00D9A3; margin-top: 16px; margin-bottom: 8px;">Select States to Filter Metrics</div>', unsafe_allow_html=True)
            
            selected_states = st.pills("Select States to Filter Metrics", states, default=states, selection_mode="multi", label_visibility="collapsed", key="state_filter")
            
            bess_df, solar_df, dc_df = load_infrastructure_data()
            
            if selected_states:
                bess_df = bess_df[bess_df['state'].isin(selected_states)]
                solar_df = solar_df[solar_df['state'].isin(selected_states)]
                dc_df = dc_df[dc_df['state'].isin(selected_states)]
            else:
                bess_df = bess_df.iloc[0:0]
                solar_df = solar_df.iloc[0:0]
                dc_df = dc_df.iloc[0:0]
                
            # 1. Build the dynamic map using the filtered dataframes
            fig = infrastructure_charts.build_infrastructure_map(bess_df, dc_df, solar_df, selected_states=selected_states)
            
            # 2. Adjust height to match the dashboard's design
            fig.update_layout(height=figure.get("height", 750), margin=dict(l=0, r=0, t=60, b=0))
            
            # 3. Render directly in Streamlit using the container
            with map_container:
                st.markdown('<div class="chart-module legacy-module">', unsafe_allow_html=True)
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": True, "scrollZoom": True})
                st.markdown('</div>', unsafe_allow_html=True)
                
            bess_operating = bess_df[bess_df['status'].astype(str).str.lower() == 'operating']
            bess_proposed = bess_df[~bess_df['status'].astype(str).str.lower().isin(['operating', 'retired'])]
            
            solar_operating = solar_df[solar_df['status'].astype(str).str.lower() == 'operating']
            solar_proposed = solar_df[~solar_df['status'].astype(str).str.lower().isin(['operating', 'retired'])]
            
            if not selected_states:
                coverage = "None"
            elif len(selected_states) == len(states):
                coverage = "NEM Only"
            else:
                coverage = ", ".join(selected_states)
            
            bess_hdre = bess_df[bess_df["source"] == "HDRE/ZEBRE Verified Data"]
            solar_hdre = solar_df[solar_df["source"] == "HDRE/ZEBRE Verified Data"]
            
            metrics = [
                {"label": "BESS Capacity", "value": f"{bess_operating['capacity_mw'].sum():,.0f} MW"},
                {"label": "Proposed BESS Capacity", "value": f"{bess_proposed['capacity_mw'].sum():,.0f} MW"},
                {"label": "BESS Sites", "value": f"{len(bess_operating):,}"},
                {"label": "Solar Capacity", "value": f"{solar_operating['capacity_mw'].sum():,.0f} MW"},
                {"label": "Proposed Solar Capacity", "value": f"{solar_proposed['capacity_mw'].sum():,.0f} MW"},
                {"label": "Solar Farms", "value": f"{len(solar_operating):,}"},
                {"label": "Data Centres", "value": f"{len(dc_df):,}"},
                {"label": "HDRE Sites", "value": f"{len(bess_hdre) + len(solar_hdre):,}"},
                {"label": "Coverage", "value": coverage}
            ]
            render_standard_metrics(metrics, entry)
            
        render_fig1_4_fragment()
    else:
        render_standard_metrics(figure.get("metrics", []), entry)
    
    takeaway = figure.get("takeaway", "")
    description = figure.get("description", "")

    if takeaway or description:
        visible_paras, source_paras, footnote_paras = split_description(description)
        zones = ['<div class="figure-notes">']
        if takeaway:
            zones.append(
                '<div class="note-zone takeaway-zone">'
                '<div class="zone-label">key takeaway</div>'
                f'<div class="takeaway-body">{format_note_text(takeaway, highlight=True)}</div>'
                "</div>"
            )
        if visible_paras:
            visible_text = format_note_text("\n\n".join(visible_paras))
            zones.append(
                '<div class="note-zone description-zone">'
                '<div class="zone-label">about this graph</div>'
                f'<div class="description-body">{visible_text}</div>'
                "</div>"
            )
        if source_paras:
            blocks = "".join(
                f'<div class="methodology-block">{format_note_text(p)}</div>' for p in source_paras
            )
            cols_class = " cols-2" if len(source_paras) > 2 else ""
            zones.append(
                '<details class="data-methodology">'
                "<summary>Data &amp; methodology</summary>"
                f'<div class="methodology-content{cols_class}">{blocks}</div>'
                "</details>"
            )
        for paragraph in footnote_paras:
            zones.append(
                f'<div class="data-footnote">{DATA_FOOTNOTE_ICON}<span>{format_note_text(paragraph)}</span></div>'
            )
        zones.append("</div>")
        st.markdown("".join(zones), unsafe_allow_html=True)


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





