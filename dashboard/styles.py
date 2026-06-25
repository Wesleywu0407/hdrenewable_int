"""Streamlit styling for the dashboard."""

from __future__ import annotations

import streamlit as st


def inject_styles() -> None:
    """Apply a dark research-terminal visual system."""
    st.markdown(
        """
        <style>
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
            background: var(--ink);
        }

        header[data-testid="stHeader"] {
            display: block !important;
            visibility: visible !important;
            height: 0 !important;
            background: transparent !important;
            pointer-events: none;
        }

        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDeployButton"],
        #MainMenu,
        footer {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
        }

        div[data-testid="stSidebarCollapseButton"] {
            display: flex !important;
            position: absolute;
            top: 20px;
            right: 14px;
            z-index: 10;
        }

        div[data-testid="stSidebarCollapseButton"] button,
        header[data-testid="stHeader"] button {
            width: 30px;
            height: 30px;
            min-height: 30px;
            padding: 0;
            border: 0.5px solid var(--line);
            border-radius: 4px;
            background: var(--panel);
            color: var(--muted);
            box-shadow: none;
            pointer-events: auto;
        }

        div[data-testid="stSidebarCollapseButton"] button:hover,
        header[data-testid="stHeader"] button:hover {
            border-color: var(--line-strong);
            background: var(--panel-2);
            color: var(--ivory);
        }

        header[data-testid="stHeader"] button {
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
            background: var(--navy);
            border-right: 0.5px solid var(--line);
        }

        section[data-testid="stSidebar"] > div {
            padding: 20px 14px 22px;
            background: var(--navy);
        }

        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 2px 4px 18px;
            margin-bottom: 12px;
            border-bottom: 0.5px solid var(--line);
        }

        .sidebar-mark {
            display: grid;
            place-items: center;
            width: 44px;
            height: 44px;
            border: 0.5px solid var(--line-strong);
            background: #0A1016;
            color: var(--ivory);
            font-size: 12px;
            font-weight: 500;
        }

        .sidebar-title {
            font-size: 12px;
            line-height: 1.2;
            text-transform: uppercase;
            color: var(--ivory);
            font-weight: 500;
        }

        .sidebar-caption {
            margin-top: 3px;
            font-size: 11px;
            color: var(--faint);
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

        .artifact-card,
        .roadmap-card {
            margin: 7px 0;
            padding: 10px 11px;
            border: 0.5px solid var(--line);
            background: #0B1117;
            border-radius: 8px;
        }

        .artifact-card.active {
            border-color: rgba(102,183,200,0.46);
            background: #101B23;
        }

        .artifact-number {
            font-size: 11px;
            line-height: 1.1;
            color: var(--faint);
            font-weight: 500;
            text-transform: uppercase;
        }

        .artifact-title {
            margin-top: 6px;
            font-size: 13px;
            line-height: 1.25;
            color: var(--ivory);
            font-weight: 500;
        }

        .artifact-status {
            margin-top: 8px;
            font-size: 11px;
            line-height: 1.2;
            color: var(--warning);
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
            width: 100%;
            min-height: 68px;
            justify-content: flex-start;
            padding: 10px 11px;
            border: 0.5px solid var(--line);
            border-radius: 8px;
            background: #0B1117;
            color: var(--muted);
            font-size: 12px;
            line-height: 1.45;
            text-align: left;
            white-space: pre-line;
            box-shadow: none;
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
            border-color: rgba(102,183,200,0.36);
            background: #101820;
            color: var(--ivory);
            box-shadow: none;
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

        .main-subtitle {
            margin-top: 10px;
            max-width: 980px;
            font-size: 14px;
            line-height: 1.5;
            color: var(--muted);
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
            min-height: 104px;
            margin-top: 12px;
            padding: 12px;
            border: 0.5px solid var(--line);
            border-radius: 8px;
            background: var(--panel-2);
        }

        .instrument-tile.compact {
            min-height: 86px;
        }

        .instrument-label {
            font-size: 11px;
            line-height: 1.2;
            color: var(--muted);
            text-transform: uppercase;
            font-weight: 500;
        }

        .instrument-value {
            margin-top: 12px;
            font-size: 28px;
            line-height: 1;
            color: var(--ivory);
            font-weight: 500;
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

        .research-note {
            margin-top: 14px;
            padding: 14px 16px;
            border-left: 2px solid var(--solar);
            border-top: 0.5px solid var(--line);
            border-right: 0.5px solid var(--line);
            border-bottom: 0.5px solid var(--line);
            border-radius: 0 8px 8px 0;
            background: #0D151C;
            color: var(--muted);
            font-size: 14px;
            line-height: 1.6;
        }

        .note-label {
            margin-bottom: 6px;
            color: var(--ivory);
            font-size: 11px;
            line-height: 1.2;
            text-transform: uppercase;
            font-weight: 500;
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
