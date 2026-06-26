"""Unified Streamlit dashboard for HDRE NEM research figures."""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
import re
from typing import Any
from urllib.parse import quote

import streamlit as st

try:
    from .config import CHAPTERS
    from .styles import inject_styles
except ImportError:
    from config import CHAPTERS
    from styles import inject_styles


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

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


def render_standard_metrics(metrics: list[dict[str, str]]) -> None:
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
            scrolling=figure.get("scrolling", False),
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
