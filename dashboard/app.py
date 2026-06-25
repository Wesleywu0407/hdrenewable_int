"""Unified Streamlit dashboard for HDRE NEM research figures."""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

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
                                <div class="artifact-title">{escape(figure.get("sidebar_title", figure["title"]).upper())}</div>
                                <div class="artifact-status">status: unpublished</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        continue

                    label = f"{figure.get('sidebar_title', figure['title']).upper()}\nstatus: published"
                    active = st.session_state.get("selected_figure") == key
                    if active:
                        st.markdown(
                            f"""
                            <div class="artifact-card active">
                                <div class="artifact-title">{escape(figure.get("sidebar_title", figure["title"]).upper())}</div>
                                <div class="artifact-status published">status: published</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    elif st.button(label, key=f"nav_{key}", use_container_width=True):
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
        iframe_height = figure.get("height", 560)
        st.components.v1.html(
            html_path.read_text(encoding="utf-8"),
            height=iframe_height,
            scrolling=False,
        )
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
    render_standard_figure(entry)


if __name__ == "__main__":
    main()
