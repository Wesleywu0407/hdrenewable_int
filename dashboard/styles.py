"""Streamlit styling for the dashboard."""

from __future__ import annotations

import streamlit as st


def inject_styles() -> None:
    """Apply a dark research-terminal visual system."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@400;500&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

        :root {
            --ink: #090D12;
            --navy: #0D141B;
            --panel: #111A22;
            --panel-2: #16212B;
            --panel-3: #1B2731;
            --ivory: #EFE8D2;
            --muted: #B9B2A3;
            --faint: #7D817C;
            --line: rgba(239,232,210,0.13);
            --line-strong: rgba(239,232,210,0.22);
            --coal: #3B3D3F;
            --gas: #C46A2B;
            --solar: #D6A21D;
            --wind: #66B7C8;
            --hydro: #557C9D;
            --battery: #5D9C58;
            --warning: #C7903A;
            --success: #78A866;
            --hairline: #262d38;
            --amber: #f5c063;
            --purple: #8f86e8;
            --body-light: #e9e7e0;
            --label-gray: #7d8590;
            --desc-gray: #9aa2ad;
        }

        html,
        body,
        [class*="css"] {
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: var(--ivory);
            font-weight: 400;
            letter-spacing: 0;
        }

        .stApp {
            background: #0D1612;
        }

        header[data-testid="stHeader"] {
            display: block !important;
            visibility: visible !important;
            height: 0 !important;
            background: transparent !important;
            pointer-events: none;
        }

        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDeployButton"],
        #MainMenu,
        footer {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
        }

        div[data-testid="stToolbar"] {
            display: block !important;
            visibility: visible !important;
            height: 0 !important;
            pointer-events: none !important;
        }

        div[data-testid="stToolbar"] button:not([data-testid="stExpandSidebarButton"]) {
            display: none !important;
        }

        button[data-testid="stExpandSidebarButton"] {
            display: none !important;
        }

        body:has(section[data-testid="stSidebar"][aria-expanded="false"])
        button[data-testid="stExpandSidebarButton"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: fixed;
            top: 14px;
            left: 14px;
            z-index: 1000;
            width: 30px;
            height: 30px;
            min-height: 30px;
            padding: 0;
            border: none !important;
            border-radius: 6px;
            background: transparent !important;
            background-color: transparent !important;
            color: #FFFFFF !important;
            box-shadow: none !important;
            pointer-events: auto !important;
        }

        body:has(section[data-testid="stSidebar"][aria-expanded="false"])
        button[data-testid="stExpandSidebarButton"]:hover {
            background-color: rgba(255, 255, 255, 0.06) !important;
            color: #FFFFFF !important;
        }

        div[data-testid="stSidebarCollapseButton"],
        div[data-testid="collapsedControl"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }

        div[data-testid="stSidebarCollapseButton"] {
            position: absolute;
            top: 20px;
            right: 14px;
            z-index: 10;
        }

        div[data-testid="stSidebarCollapseButton"] button,
        div[data-testid="collapsedControl"] button {
            width: 30px;
            height: 30px;
            min-height: 30px;
            padding: 0;
            border: none !important;
            border-radius: 6px;
            background: transparent !important;
            background-color: transparent !important;
            color: #FFFFFF !important;
            box-shadow: none !important;
            pointer-events: auto;
            visibility: visible !important;
            opacity: 1 !important;
        }

        div[data-testid="stSidebarCollapseButton"] button:hover,
        div[data-testid="collapsedControl"] button:hover {
            background-color: rgba(255, 255, 255, 0.06) !important;
            color: #FFFFFF !important;
        }

        div[data-testid="stSidebarCollapseButton"] button svg,
        div[data-testid="collapsedControl"] button svg,
        button[data-testid="stExpandSidebarButton"] svg,
        button[data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"],
        button[kind="header"][data-testid="baseButton-headerNoPadding"] svg,
        button[kind="headerNoPadding"] [data-testid="stIconMaterial"],
        [data-testid="stSidebarCollapsedControl"] button svg {
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
            opacity: 1 !important;
        }

        /* Floating expand button (visible when sidebar is collapsed) */
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"],
        button[data-testid="stSidebarCollapsedControl"],
        button[data-testid="stExpandSidebarButton"],
        button[kind="headerNoPadding"] {
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        [data-testid="stSidebarCollapsedControl"] button,
        [data-testid="collapsedControl"] button {
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        [data-testid="stSidebarCollapsedControl"] svg,
        [data-testid="collapsedControl"] svg,
        [data-testid="stSidebarCollapsedControl"] button svg,
        [data-testid="collapsedControl"] button svg,
        button[data-testid="stExpandSidebarButton"] svg,
        button[data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"] {
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
            opacity: 1 !important;
        }

        [data-testid="stSidebarCollapsedControl"]:hover,
        [data-testid="collapsedControl"]:hover,
        [data-testid="stSidebarCollapsedControl"] button:hover,
        [data-testid="collapsedControl"] button:hover,
        button[data-testid="stExpandSidebarButton"]:hover {
            background-color: rgba(255, 255, 255, 0.06) !important;
            border-radius: 6px !important;
        }

        div[data-testid="collapsedControl"] {
            position: fixed;
            top: 14px;
            left: 14px;
            z-index: 1000;
        }

        section.main > div,
        div[data-testid="stAppViewContainer"] > .main .block-container {
            max-width: 1660px;
            padding: 20px 30px 36px !important;
        }

        section[data-testid="stSidebar"] {
            width: 310px !important;
            min-width: 310px !important;
            background-color: #070E0C !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        section[data-testid="stSidebar"] > div {
            padding: 20px 14px 22px;
            background-color: #070E0C !important;
        }

        /* Pull sidebar content to the top - reduce excessive top padding */
        section[data-testid="stSidebar"] > div:first-child,
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            padding-top: 24px !important;
            margin-top: 0 !important;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
            display: block !important;
            height: 0 !important;
            min-height: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
            overflow: visible !important;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }

        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"]:first-child {
            padding-top: 0 !important;
            gap: 0 !important;
        }

        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 0 !important;
        }

        .hdre-branding {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }

        section.main,
        div[data-testid="stAppViewContainer"] > section.main {
            background-color: #0D1612 !important;
        }

        /* HDRE branding block */
        .hdre-branding {
            padding: 20px 16px 24px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .hdre-wordmark-link {
            display: inline-block;
            text-decoration: none !important;
            border-bottom: none !important;
            cursor: pointer;
        }

        .hdre-wordmark-link:hover,
        .hdre-wordmark-link:active,
        .hdre-wordmark-link:visited,
        .hdre-wordmark-link:focus {
            text-decoration: none !important;
            border-bottom: none !important;
        }

        .hdre-wordmark {
            font-family: 'Fraunces', Georgia, serif !important;
            font-size: 28px !important;
            font-weight: 500 !important;
            color: #00D9A3 !important;
            letter-spacing: 0.02em !important;
            line-height: 1 !important;
            transition: color 0.15s ease;
            text-decoration: none !important;
            border-bottom: none !important;
            pointer-events: none;
        }

        .hdre-wordmark-link:hover .hdre-wordmark,
        .hdre-wordmark-link:focus .hdre-wordmark,
        .hdre-branding:hover .hdre-wordmark {
            color: #F5F5F0 !important;
        }

        .hdre-divider {
            width: 60px;
            height: 1px;
            background-color: rgba(255, 255, 255, 0.12);
            margin: 6px 0 8px 0;
        }

        .hdre-label {
            font-family: 'Inter', system-ui, sans-serif;
            font-size: 11px;
            font-weight: 500;
            color: #6B7570;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .hdre-subtitle {
            font-family: 'Inter', system-ui, sans-serif;
            font-size: 12px;
            font-weight: 400;
            color: #B8BDB9;
            margin-top: 2px;
        }

        .chapter-strip {
            margin: 18px 4px 9px;
            padding-top: 10px;
            border-top: 0.5px solid var(--line);
            font-size: 11px;
            line-height: 1.3;
            color: var(--muted);
            text-transform: uppercase;
        }

        section[data-testid="stSidebar"] div[data-testid="stExpander"] {
            margin-top: 10px;
            margin-bottom: 28px !important;
            border: 0;
            border-top: 0.5px solid var(--line);
            border-radius: 0;
            background: transparent;
        }

        section[data-testid="stSidebar"] div[data-testid="stExpander"] details {
            margin-bottom: 0 !important;
            border: 0;
            background: transparent;
        }

        section[data-testid="stSidebar"] div[data-testid="stExpander"] summary {
            position: relative;
            min-height: 0;
            padding: 9px 6px 9px;
            border: 0 !important;
            border-radius: 4px;
            outline: 0 !important;
            background: transparent !important;
            color: var(--faint) !important;
            font-family: "SFMono-Regular", Consolas, monospace;
            font-size: 12px;
            line-height: 1.35;
            text-transform: uppercase;
            letter-spacing: 0.035em;
            box-shadow: none !important;
            cursor: pointer;
            transition: color 140ms ease, background-color 140ms ease, padding-left 140ms ease;
        }

        section[data-testid="stSidebar"] div[data-testid="stExpander"] summary:hover {
            color: #F5F5F0 !important;
            background-color: rgba(0, 217, 163, 0.04) !important;
            padding-left: 9px;
        }

        section[data-testid="stSidebar"] div[data-testid="stExpander"] details[open] > summary {
            color: var(--muted) !important;
            background: rgba(255,255,255,0.018) !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stExpander"] details[open] > summary::before {
            content: "";
            position: absolute;
            left: 0;
            top: 9px;
            bottom: 7px;
            width: 1px;
            background: rgba(102,183,200,0.62);
        }

        section[data-testid="stSidebar"] div[data-testid="stExpander"] summary p {
            font-size: inherit;
            line-height: inherit;
            color: inherit !important;
            white-space: normal;
            word-break: normal;
            overflow-wrap: anywhere;
        }

        section[data-testid="stSidebar"] div[data-testid="stExpander"] summary > span {
            color: inherit !important;
            background: transparent !important;
            transition: color 140ms ease;
        }

        section[data-testid="stSidebar"] div[data-testid="stExpander"] details[open] > summary > span,
        section[data-testid="stSidebar"] div[data-testid="stExpander"] summary:hover > span {
            color: inherit !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stExpander"] summary svg {
            color: inherit !important;
            transition: color 140ms ease;
        }

        /* Chapter expand/collapse chevron arrow */
        section[data-testid="stSidebar"] [data-testid="stExpander"] summary svg,
        section[data-testid="stSidebar"] details > summary svg,
        section[data-testid="stSidebar"] [data-testid="stExpander"] summary [data-testid="stIconMaterial"],
        section[data-testid="stSidebar"] details > summary [data-testid="stIconMaterial"],
        section[data-testid="stSidebar"] .chapter-toggle svg {
            color: #6B7570 !important;
            fill: #6B7570 !important;
            opacity: 1 !important;
            transition: color 0.15s ease, fill 0.15s ease;
        }

        section[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover svg,
        section[data-testid="stSidebar"] details > summary:hover svg,
        section[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover [data-testid="stIconMaterial"],
        section[data-testid="stSidebar"] details > summary:hover [data-testid="stIconMaterial"],
        section[data-testid="stSidebar"] .chapter-toggle:hover svg {
            color: #00D9A3 !important;
            fill: #00D9A3 !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
            padding: 0;
        }

        .artifact-card,
        .roadmap-card {
            display: block;
            position: relative;
            margin: 3px 0;
            padding: 6px 9px 6px 11px;
            border: 0;
            border-bottom: 0.5px solid var(--line);
            background: transparent;
            border-radius: 4px;
            color: inherit;
            text-decoration: none;
            cursor: pointer;
            transition: background-color 140ms ease, border-color 140ms ease, color 140ms ease;
        }

        .artifact-card.active {
            border-left: 2px solid var(--wind);
            border-bottom-color: var(--line);
            background: rgba(102,183,200,0.07);
        }

        .artifact-number {
            font-size: 11px;
            line-height: 1.1;
            color: var(--faint);
            font-weight: 500;
            text-transform: uppercase;
        }

        .artifact-title {
            margin-top: 2px;
            font-size: 13px;
            line-height: 1.25;
            color: var(--ivory);
            font-weight: 500;
        }

        .artifact-dot {
            display: inline-block;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            margin-right: 8px;
            vertical-align: middle;
            border: 0;
            opacity: 0.45;
            box-shadow: none;
            transition: opacity 0.15s ease, box-shadow 0.15s ease;
        }

        .artifact-dot.dot-published { background: #00D9A3; }
        .artifact-dot.dot-draft     { background: #FAC775; }
        .artifact-dot.dot-planned   { background: rgba(255,255,255,0.2); }

        .artifact-card:hover,
        .artifact-card:hover .artifact-title {
            text-decoration: none;
        }

        .artifact-card:hover {
            border-bottom-color: rgba(102,183,200,0.34);
            background-color: rgba(0, 217, 163, 0.06) !important;
            color: #F5F5F0 !important;
        }

        .artifact-card:hover .artifact-dot {
            opacity: 0.75 !important;
        }

        .artifact-card.active .artifact-dot {
            opacity: 1 !important;
            box-shadow: 0 0 0 6px rgba(0, 217, 163, 0.25) !important;
        }

        .artifact-card:hover .artifact-title,
        .artifact-card.active .artifact-title {
            color: #F5EFD9;
        }

        .artifact-status {
            display: inline-block;
            margin-top: 4px;
            padding: 2px 5px;
            border: 0.5px solid currentColor;
            border-radius: 999px;
            font-family: "SFMono-Regular", Consolas, monospace;
            font-size: 8px;
            line-height: 1.2;
            color: var(--warning);
            opacity: 0.72;
        }

        .artifact-status.published {
            color: var(--success);
        }

        .roadmap-card {
            opacity: 0.62;
        }

        .roadmap-subtitle {
            margin-top: 6px;
            font-size: 11px;
            line-height: 1.35;
            color: var(--faint);
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button {
            display: block;
            position: relative;
            margin: 3px 0;
            padding: 6px 9px 6px 11px;
            border: 0;
            border-bottom: 0.5px solid var(--line);
            background: transparent;
            border-radius: 4px;
            color: var(--ivory);
            font-size: 13px;
            font-weight: 500;
            line-height: 1.25;
            text-align: left;
            width: 100%;
            min-height: auto;
            justify-content: flex-start;
            box-shadow: none;
            transition: background-color 140ms ease, border-color 140ms ease, color 140ms ease;
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button p {
            font-size: 13px;
            font-weight: 500;
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
            border-bottom-color: rgba(102,183,200,0.34);
            background-color: rgba(0, 217, 163, 0.06) !important;
            color: #F5F5F0 !important;
            box-shadow: none;
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] {
            border-left: 2px solid var(--wind);
            border-bottom-color: var(--line);
            background: rgba(102,183,200,0.07);
            color: #F5EFD9;
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button::before {
            content: "";
            display: inline-block;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            margin-right: 8px;
            vertical-align: middle;
            background: #00D9A3;
            opacity: 0.45;
            transition: opacity 0.15s ease, box-shadow 0.15s ease;
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover::before {
            opacity: 0.75 !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"]::before {
            opacity: 1 !important;
            box-shadow: 0 0 0 6px rgba(0, 217, 163, 0.25) !important;
        }

        .sidebar-footer {
            margin: 26px 4px 0;
            padding-top: 14px;
            border-top: 0.5px solid var(--line);
        }

        .sidebar-footer-label {
            margin-bottom: 8px;
            font-size: 11px;
            color: var(--faint);
            text-transform: uppercase;
            font-weight: 500;
        }

        .sidebar-footer-row {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            padding: 5px 0;
            font-size: 12px;
            color: var(--muted);
        }

        .sidebar-footer-row span:last-child {
            color: var(--ivory);
        }

        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 18px;
            margin-bottom: 22px;
            padding: 12px 14px;
            border: 0.5px solid var(--line);
            background: var(--panel);
            border-radius: 8px;
        }

        .terminal-label {
            font-size: 13px;
            line-height: 1.2;
            color: var(--ivory);
            font-weight: 500;
            text-transform: uppercase;
        }

        .terminal-meta,
        .system-state {
            margin-top: 3px;
            font-size: 12px;
            color: var(--muted);
        }

        .system-state {
            margin-top: 0;
            text-align: right;
            color: var(--wind);
            white-space: nowrap;
        }

        .figure-kicker {
            margin: 0 0 8px;
            font-size: 12px;
            line-height: 1.35;
            color: var(--wind);
            text-transform: uppercase;
            font-weight: 500;
        }

        .main-title {
            margin: 0;
            max-width: 980px;
            font-size: clamp(26px, 2.1vw, 38px);
            line-height: 1.08;
            color: var(--ivory);
            font-weight: 500;
        }

        .hero-title,
        .main-title,
        div[data-testid="stMarkdownContainer"] h1,
        section.main h1 {
            color: #F5F5F0 !important;
            opacity: 1 !important;
            font-weight: 500 !important;
            font-family: 'Fraunces', Georgia, serif !important;
            font-size: 26px !important;
            line-height: 1.3 !important;
            margin-bottom: 24px !important;
        }

        .main-subtitle {
            margin-top: -4px !important;
            margin-bottom: 12px !important;
            max-width: 980px;
            font-size: 13px !important;
            line-height: 1.5;
            color: #6B7570 !important;
            font-weight: 400 !important;
            letter-spacing: 0 !important;
            text-transform: none !important;
        }

        div[data-testid="stDownloadButton"] button,
        div[data-testid="stButton"] button {
            min-height: 32px;
            padding: 6px 10px;
            border: 0.5px solid var(--line-strong);
            border-radius: 4px;
            background: var(--panel-2);
            color: var(--ivory);
            font-size: 12px;
            line-height: 1.2;
            font-weight: 400;
            box-shadow: none;
        }

        div[data-testid="stDownloadButton"] button:hover,
        div[data-testid="stButton"] button:hover {
            border-color: rgba(214,162,29,0.55);
            background: var(--panel-3);
            color: var(--solar);
            box-shadow: none;
        }

        div[data-testid="stDownloadButton"] button:disabled,
        div[data-testid="stButton"] button:disabled {
            background: #10161C;
            color: var(--faint);
            border-color: var(--line);
        }

        .chart-module {
            margin-top: 20px;
            padding: 12px;
            border: 0.5px solid var(--line);
            border-radius: 8px;
            background: var(--panel);
        }

        .chart-module:empty {
            display: none !important;
        }

        .hero-module {
            padding: 8px 8px 0;
            background: #0A1015;
        }

        .legacy-module {
            background: #0A1015;
        }

        .legacy-module iframe {
            background: #FFFFFF;
            border-radius: 4px;
            opacity: 0.9;
        }

        iframe {
            width: 100% !important;
            border: none !important;
            overflow: hidden !important;
        }

        .instrument-tile {
            min-height: 96px;
            margin-top: 12px;
            padding: 14px 16px;
            border: 0;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.03);
        }

        .instrument-tile.compact {
            min-height: 80px;
        }

        .instrument-label {
            font-size: 11px;
            line-height: 1.4;
            color: var(--label-gray);
            letter-spacing: 0.14em;
            text-transform: uppercase;
            font-weight: 500;
        }

        .instrument-value {
            margin-top: 10px;
            font-size: 24px;
            line-height: 1;
            color: var(--ivory);
            font-weight: 500;
        }

        /* KPI card value - use monospace for that data-terminal feel */
        .kpi-card .instrument-value,
        .kpi-card .kpi-value,
        .kpi-card [data-testid="metric-value"],
        .kpi-value {
            font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace !important;
            font-feature-settings: 'tnum' on, 'lnum' on !important;
            letter-spacing: -0.01em !important;
        }

        .instrument-value span {
            margin-left: 5px;
            font-size: 12px;
            color: var(--faint);
            font-weight: 400;
        }

        .instrument-note {
            margin-top: 12px;
            padding-top: 9px;
            border-top: 0.5px solid var(--line);
            font-size: 11px;
            line-height: 1.35;
            color: var(--faint);
        }

        /* Editorial figure notes: flat zones on page background, hairline dividers, no boxes */
        .figure-notes {
            margin-top: 36px;
        }

        .note-zone + .note-zone {
            margin-top: 36px;
        }

        .zone-label {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 16px;
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--label-gray);
        }

        .zone-label::after {
            content: "";
            flex: 1 1 auto;
            height: 0.5px;
            background: var(--hairline);
        }

        .takeaway-body {
            max-width: 64ch;
            font-size: 19px;
            line-height: 1.75;
            font-weight: 400;
            color: var(--body-light);
        }

        .takeaway-body strong,
        .description-body strong,
        .methodology-block strong {
            font-weight: 500;
            color: inherit;
        }

        .hl-amber { color: var(--amber); }
        .hl-purple { color: var(--purple); }

        .description-body {
            max-width: 64ch;
            font-size: 14px;
            line-height: 1.7;
            color: var(--desc-gray);
        }

        .note-label {
            margin-bottom: 8px;
            font-size: 11px;
            line-height: 1.4;
            font-weight: 500;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--label-gray);
        }

        .takeaway-body .note-label,
        .methodology-block .note-label {
            margin-top: 14px;
        }

        .takeaway-body .note-label:first-child,
        .methodology-block .note-label:first-child {
            margin-top: 0;
        }

        .data-methodology {
            margin-top: 32px;
        }

        .data-methodology summary {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 5px 14px;
            border: 0.5px solid var(--hairline);
            border-radius: 999px;
            font-size: 12px;
            color: var(--label-gray);
            list-style: none;
            cursor: pointer;
            user-select: none;
            transition: color 140ms ease, border-color 140ms ease;
        }

        .data-methodology summary::-webkit-details-marker {
            display: none;
        }

        .data-methodology summary::before {
            content: "";
            width: 5px;
            height: 5px;
            border-right: 1px solid currentColor;
            border-bottom: 1px solid currentColor;
            transform: rotate(45deg) translateY(-1px);
            transition: transform 140ms ease;
        }

        .data-methodology[open] summary::before {
            transform: rotate(225deg);
        }

        .data-methodology summary:hover {
            color: var(--ivory);
            border-color: var(--line-strong);
        }

        .methodology-content {
            margin-top: 16px;
            max-width: 110ch;
            font-size: 12.5px;
            line-height: 1.7;
            color: var(--label-gray);
        }

        .methodology-block {
            break-inside: avoid;
            margin-bottom: 14px;
        }

        @media (min-width: 1100px) {
            .methodology-content.cols-2 {
                column-count: 2;
                column-gap: 48px;
            }
        }

        .data-footnote {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 32px;
            font-size: 12.5px;
            color: var(--label-gray);
        }

        .data-footnote svg {
            flex: 0 0 auto;
            opacity: 0.75;
        }

        .stat-single {
            margin-top: 32px;
            max-width: 64ch;
        }

        .stat-single-value {
            font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
            font-feature-settings: 'tnum' on, 'lnum' on;
            font-size: 33px;
            line-height: 1.15;
            font-weight: 500;
            letter-spacing: -0.01em;
        }

        .missing-file {
            padding: 18px;
            border: 0.5px solid rgba(199,144,58,0.45);
            border-radius: 8px;
            background: #19150E;
            color: var(--warning);
            font-size: 14px;
            line-height: 1.5;
        }

        div[data-testid="stPlotlyChart"] {
            background: transparent;
        }

        @media (max-width: 980px) {
            div[data-testid="stAppViewContainer"] > .main .block-container {
                padding: 16px 18px 28px !important;
            }

            .topbar {
                align-items: flex-start;
                flex-direction: column;
            }

            .system-state {
                text-align: left;
            }

            .main-title {
                font-size: 26px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
