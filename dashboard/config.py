"""Dashboard content configuration.

Add or update chapters and figures here. The Streamlit UI should read this
structure directly, so adding a new figure does not require app code changes.
"""

from __future__ import annotations


CHAPTERS = [
    {
        "id": "1.2",
        "title": "NEM grid analysis",
        "subtitle": "National Electricity Market Grid Analysis",
        "status": "done",
        "figures": [
            {
                "id": "fig1",
                "number": 1,
                "title": "NEM real-time generation mix",
                "sidebar_title": "LIVE GENERATION MIX",
                "subtitle": "NEM Real-time Generation Mix (Past 7 Days)",
                "html_path": "outputs/figures/fig1_nem_realtime_mix.html",
                "png_path": "outputs/figures/png/fig1_nem_realtime_mix.png",
                "metrics": [
                    {"label": "Coal", "value": "53.3%"},
                    {"label": "Wind", "value": "18.5%"},
                    {"label": "Solar", "value": "12.1%"},
                ],
                "takeaway": (
                    "Coal remains the grid backbone, while midday solar and sunset "
                    "firming demand are already creating the duck-curve dynamics that "
                    "make storage and flexible capacity commercially attractive."
                ),
            },
            {
                "id": "fig2",
                "number": 2,
                "title": "NEM monthly generation by fuel type",
                "sidebar_title": "MONTHLY FUEL TYPE",
                "subtitle": "NEM Monthly Generation by Fuel Type",
                "html_path": "outputs/figures/fig2_annual_generation_by_fuel.html",
                "png_path": "outputs/figures/png/fig2_annual_generation_by_fuel.png",
                "metrics": [
                    {"label": "Coal average", "value": "52.3%"},
                    {"label": "Solar average", "value": "21.5%"},
                    {"label": "Wind average", "value": "15.6%"},
                ],
                "takeaway": (
                    "Even within the available 2024-06 to 2026-06 window, zero-marginal-cost "
                    "solar and wind are visibly eroding coal's share, with seasonal solar "
                    "peaks reshaping the monthly mix."
                ),
            },
            {
                "id": "fig3",
                "number": 3,
                "title": "Generation mix by state",
                "sidebar_title": "STATE MIX",
                "subtitle": "Generation Mix by State (Latest 12 Months)",
                "html_path": "outputs/figures/fig3_state_comparison.html",
                "png_path": "outputs/figures/png/fig3_state_comparison.png",
                "metrics": [
                    {"label": "QLD coal", "value": "59.2%"},
                    {"label": "NSW coal", "value": "57.6%"},
                    {"label": "SA coal", "value": "0%"},
                ],
                "takeaway": (
                    "South Australia shows a near-fully-renewable synchronous grid in "
                    "operation, while QLD and NSW remain the largest decarbonisation and "
                    "investment headroom in the NEM."
                ),
            },
            {
                "id": "fig4",
                "number": 4,
                "title": "Renewable energy share by state",
                "sidebar_title": "RENEWABLE SHARE",
                "subtitle": "Renewable Energy Share by State",
                "html_path": "outputs/figures/fig4_renewable_share_evolution.html",
                "png_path": "outputs/figures/png/fig4_renewable_share_evolution.png",
                "metrics": [
                    {"label": "TAS renewable", "value": "99.2%"},
                    {"label": "SA renewable", "value": "70-74%"},
                    {"label": "QLD renewable", "value": "32%"},
                ],
                "takeaway": (
                    "The gap between TAS near 99% and QLD near 32% shows that Australia "
                    "does not have a single renewable trajectory; partnership and "
                    "procurement strategy must be region-specific."
                ),
            },
            {
                "id": "fig5",
                "number": 5,
                "title": "NEM coal unit operating and retirement timeline",
                "sidebar_title": "COAL RETIREMENT TIMELINE",
                "subtitle": "NEM Coal Unit Operating & Retirement Timeline",
                "html_path": "outputs/figures/fig5_coal_retirement_timeline.html",
                "png_path": "outputs/figures/png/fig5_coal_retirement_timeline.png",
                "metrics": [
                    {"label": "Retired units", "value": "43"},
                    {"label": "Operating units", "value": "44"},
                    {"label": "Retiring by 2035", "value": "12.9 GW"},
                ],
                "takeaway": (
                    "Expected coal retirements create a large, date-certain capacity gap "
                    "that must be filled by renewables and firming, making the timeline a "
                    "practical map for project development and offtake positioning."
                ),
            },
        ],
    },
    {
        "id": "1.1",
        "title": "Queensland renewables",
        "subtitle": "Queensland Renewable Energy Development",
        "status": "wip",
        "figures": [],
    },
    {
        "id": "2.1",
        "title": "Electricity trading market",
        "subtitle": "Electricity Trading Market Volatility",
        "status": "planned",
        "figures": [],
    },
    {
        "id": "3.1",
        "title": "AI data center demand",
        "subtitle": "AI Data Center Demand Impact",
        "status": "planned",
        "figures": [],
    },
]
