"""Sidebar navigation component."""

from __future__ import annotations

from collections.abc import Callable
from html import escape
from typing import Any

import streamlit as st


def render_sidebar(
    figures: list[dict[str, Any]],
    chapters: list[dict[str, Any]],
    figure_key: Callable[[dict[str, Any], dict[str, Any]], str],
) -> None:
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

        for chapter in chapters:
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
                            type="primary" if active else "secondary",
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
