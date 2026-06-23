"""Dashboard content configuration.

Add or update chapters and figures here. The Streamlit UI should read this
structure directly, so adding a new figure does not require app code changes.
"""

from __future__ import annotations


CHAPTERS = [
    {
        "id": "1.1",
        "title": "Queensland renewables",
        "subtitle": "Queensland Renewable Energy Development",
        "status": "done",
        "figures": [
            {
                "id": "fig1_1",
                "number": 1,
                "title": "QLD Renewable Share vs Peers",
                "sidebar_title": "RENEWABLE SHARE",
                "subtitle": "QLD vs NSW Renewable Generation Share",
                "html_path": "outputs/figures/fig1_1_qld_renewable_share.html",
                "png_path": "outputs/figures/png/fig1_1_qld_renewable_share.png",
                "metrics": [
                    {"label": "QLD renewable", "value": "Rising"},
                    {"label": "Comparison", "value": "Converging"}
                ],
                "takeaway": (
                    "QLD is accelerating its renewable deployment and converging with its peer state NSW."
                ),
            },
            {
                "id": "fig1_2",
                "number": 2,
                "title": "QLD Fuel Mix Evolution",
                "sidebar_title": "FUEL MIX EVOLUTION",
                "subtitle": "QLD Generation Mix Evolution (Last 24 Months)",
                "html_path": "outputs/figures/fig1_2_qld_fuel_mix.html",
                "png_path": "outputs/figures/png/fig1_2_qld_fuel_mix.png",
                "metrics": [
                    {"label": "Renewables", "value": "Increasing"}
                ],
                "takeaway": (
                    "The past 24 months show a steady increase in renewable penetration in Queensland's fuel mix."
                ),
            },
            {
                "id": "fig1_3",
                "number": 3,
                "title": "QLD Negative Spot-Price Frequency",
                "sidebar_title": "NEGATIVE PRICES",
                "subtitle": "Monthly Hours below $0/MWh",
                "html_path": "outputs/figures/fig1_3_qld_negative_prices.html",
                "png_path": "outputs/figures/png/fig1_3_qld_negative_prices.png",
                "metrics": [
                    {"label": "Price Volatility", "value": "High"}
                ],
                "takeaway": (
                    "High instances of negative spot prices indicate excess solar generation during midday."
                ),
            }
        ],
    },
    {
        "id": "1.2",
        "title": "National Electricity Market grid analysis",
        "subtitle": "National Electricity Market Grid Analysis",
        "status": "done",
        "figures": [
            {
                "id": "fig1",
                "number": 1,
                "title": "NEM real-time generation mix",
                "sidebar_title": "LIVE GENERATION MIX",
                "subtitle": "NEM Real-time Generation Mix & Price (Past 7 Days)",
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
                "title": "NEM-wide monthly generation by fuel type",
                "sidebar_title": "NEM-WIDE FUEL MIX",
                "subtitle": "National Electricity Market (All Regions) Monthly Generation",
                "html_path": "outputs/figures/fig2_annual_generation_by_fuel.html",
                "png_path": "outputs/figures/png/fig2_annual_generation_by_fuel.png",
                "metrics": [
                    {"label": "Coal average", "value": "52.3%"},
                    {"label": "Solar average", "value": "21.5%"},
                    {"label": "Wind average", "value": "15.6%"},
                ],
                "takeaway": (
                    "Even within the available 2024-06 to 2026-06 window, zero-marginal-cost "
                    "solar and wind are visibly eroding coal's share across the entire NEM, "
                    "with seasonal solar peaks reshaping the monthly mix."
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
                "title": "NEM coal unit operating and retirement timeline",
                "sidebar_title": "COAL RETIREMENT TIMELINE",
                "subtitle": "NEM Coal Unit Operating & Retirement Timeline",
                "html_path": "outputs/figures/fig4_coal_retirement_timeline.html",
                "png_path": "outputs/figures/png/fig4_coal_retirement_timeline.png",
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
