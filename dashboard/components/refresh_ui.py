"""Refresh status and run-details UI component."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from html import escape
from typing import Any

import streamlit as st

from dashboard.utils import (
    format_refresh_time,
    format_run_duration,
    is_refresh_stale,
    parse_refresh_datetime,
    parse_refresh_log,
    render_html,
    simplify_refresh_error,
)
from scripts.common.paths import LOG_DIR, PROJECT_ROOT, RUNTIME_DIR

REFRESH_STATUS_DIR = RUNTIME_DIR / "refresh"

REFRESH_REGISTRY = {
    "1.2::*": {
        "scope_label": "National Electricity Market grid data",
        "button_label": "Refresh",
        "command": ["bash", "scripts/chapter_1/run_nem_scrape.sh"],
        "status_path": REFRESH_STATUS_DIR / "chapter_1_2_status.json",
        "log_path": LOG_DIR / "chapter_1_2_refresh.log",
        "expected_outputs": [
            "outputs/figures/fig1_nem_realtime_mix.html",
            "outputs/figures/fig2_annual_generation_by_fuel.html",
            "outputs/figures/fig3_state_comparison.html",
        ],
    },
}


def _entry_key(entry: dict[str, Any]) -> str:
    return f"{entry['chapter']['id']}::{entry['figure']['id']}"


def refresh_config_for_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    exact_key = _entry_key(entry)
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

    status_col, button_col, log_col = st.columns([0.62, 0.18, 0.20], gap="small")
    with status_col:
        st.markdown(
            f"""
            <div class="analysis-refresh-status">
                <span class="refresh-pill" style="
                    color: {pill_color};
                    border-color: color-mix(in srgb, {pill_color} 56%, transparent);
                    background: color-mix(in srgb, {pill_color} 10%, transparent);
                ">{pill_text}</span>
                <span class="refresh-time">
                    <span>{escape(time_label)}</span> {escape(last_updated_text)}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with button_col:
        st.markdown('<div class="refresh-primary-action">', unsafe_allow_html=True)
        if "pyodide" not in sys.modules and st.button(config["button_label"], width="content"):
            with st.spinner(f"Refreshing {config['scope_label']}..."):
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
