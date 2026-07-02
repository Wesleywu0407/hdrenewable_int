"""Unified Streamlit dashboard for HDRE NEM research figures."""

from __future__ import annotations

import re
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import quote

import streamlit as st

from scripts.chapter_1 import generate_infrastructure_charts as infrastructure_charts

try:
    from .components.refresh_ui import render_refresh_control
    from .components.sidebar import render_sidebar
    from .config import CHAPTERS
    from .data import load_infrastructure_data
    from .styles import inject_styles
    from .utils import render_html
except ImportError:
    from components.refresh_ui import render_refresh_control
    from components.sidebar import render_sidebar
    from config import CHAPTERS
    from styles import inject_styles
    from utils import render_html

    from data import load_infrastructure_data


PROJECT_ROOT = Path(__file__).resolve().parents[1]

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
                <div class="terminal-meta">{escape(source_label)} · Updated {UPDATED_DATE:%d %b %Y} · Chapter {escape(chapter["id"])}</div>
            </div>
            {system_state_html}
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

        def amber_repl(match: re.Match, highlight_counts=counts) -> str:
            if highlight_counts["amber"] >= 2:
                return match.group(0)
            highlight_counts["amber"] += 1
            return f'<span class="hl-amber">{match.group(0)}</span>'

        def purple_repl(match: re.Match, highlight_counts=counts) -> str:
            if highlight_counts["purple"] >= 1:
                return match.group(0)
            highlight_counts["purple"] += 1
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
    render_sidebar(figures, CHAPTERS, figure_key)
    entry = selected_entry(figures)
    if not entry:
        st.warning("No figures configured.")
        return

    render_header(entry)
    render_refresh_control(entry)
    render_standard_figure(entry)


if __name__ == "__main__":
    main()
