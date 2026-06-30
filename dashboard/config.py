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
        "source": "OpenElectricity API",
        "figures": [
            {
                "id": "fig1_1",
                "number": 1,
                "title": "QLD Renewable Share vs Peers",
                "sidebar_title": "RENEWABLE SHARE",
                "subtitle": "QLD vs NSW Renewable Generation Share",
                "html_path": "outputs/figures/fig1_1_qld_renewable_share.html",
                "png_path": "outputs/figures/png/fig1_1_qld_renewable_share.png",
                "source": "OpenElectricity API",
                "metrics": [
                    {"label": "QLD renewable", "value": "Rising"},
                    {"label": "Comparison", "value": "Converging"}
                ],
                "takeaway": (
                    "QLD is accelerating its renewable deployment and converging with its peer state NSW."
                ),
                "description": (
                    "This graph compares the percentage of total electricity generated from renewable sources (solar, wind, hydro, bioenergy) in Queensland against New South Wales over time. It illustrates the relative pace at which these two major states are transitioning away from fossil fuels.\n\nData is based off scripts/03_fetch_qld_data.py and charted by scripts/04_generate_qld_charts.py."
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
                "source": "OpenElectricity API",
                "metrics": [
                    {"label": "Renewables", "value": "Increasing"}
                ],
                "takeaway": (
                    "The past 24 months show a steady increase in renewable penetration in Queensland's fuel mix."
                ),
                "description": (
                    "This area chart visualizes the total volume of electricity generated in Queensland by different fuel types (coal, gas, solar, wind, etc.) over the past 24 months. It highlights the changing proportions and seasonal variations of each generation source.\n\nData is based off scripts/03_fetch_qld_data.py and charted by scripts/04_generate_qld_charts.py."
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
                "source": "OpenElectricity API",
                "metrics": [
                    {"label": "Price Volatility", "value": "High"}
                ],
                "takeaway": (
                    "High instances of negative spot prices indicate excess solar generation during midday."
                ),
                "description": (
                    "This bar chart tracks the frequency of negative wholesale electricity spot prices in Queensland. A negative spot price occurs when the supply of electricity exceeds demand, often during periods of high solar generation, meaning generators effectively pay the market to take their power.\n\nData is based off scripts/03_fetch_qld_data.py and charted by scripts/04_generate_qld_charts.py."
                ),
            }
        ],
    },
    {
        "id": "1.2",
        "title": "National Electricity Market grid analysis",
        "subtitle": "National Electricity Market Grid Analysis",
        "status": "done",
        "source": "OpenElectricity API",
        "figures": [
            {
                "id": "fig1",
                "number": 1,
                "title": "NEM real-time generation mix",
                "sidebar_title": "LIVE GENERATION MIX",
                "subtitle": "NEM Real-time Generation Mix & Price (Past 7 Days)",
                "html_path": "outputs/figures/fig1_nem_realtime_mix.html",
                "png_path": "outputs/figures/png/fig1_nem_realtime_mix.png",
                "source": "OpenElectricity API",
                # Note: metrics for fig1 are computed live via realtime_metrics()
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
                "description": (
                    "This interactive chart stacks the real-time electricity generation from all fuel types across the National Electricity Market (NEM) to show total demand over the past 7 days. The overlaid dashed line represents the wholesale electricity spot price (in AUD/MWh) during those same intervals.\n\nData is based off scripts/01_fetch_nem_data.py and charted by scripts/02_generate_charts.py."
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
                "source": "OpenElectricity API",
                "metrics": [
                    {"label": "Coal average", "value": "52.3%", "note": "as of last data refresh"},
                    {"label": "Solar average", "value": "21.5%", "note": "as of last data refresh"},
                    {"label": "Wind average", "value": "15.6%", "note": "as of last data refresh"},
                ],
                "takeaway": (
                    "Even within the available 2024-06 to 2026-06 window, zero-marginal-cost "
                    "solar and wind are visibly eroding coal's share across the entire NEM, "
                    "with seasonal solar peaks reshaping the monthly mix."
                ),
                "description": (
                    "This stacked bar chart aggregates the total monthly electricity generation across all NEM regions, broken down by fuel type. It reveals how seasonal weather patterns (affecting solar and wind output) and long-term trends shape the overall grid energy mix.\n\nData is based off scripts/01_fetch_nem_data.py and charted by scripts/02_generate_charts.py."
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
                "source": "OpenElectricity API",
                "metrics": [
                    {"label": "QLD coal", "value": "59.2%", "note": "as of last data refresh"},
                    {"label": "NSW coal", "value": "57.6%", "note": "as of last data refresh"},
                    {"label": "SA coal", "value": "0%", "note": "as of last data refresh"},
                ],
                "takeaway": (
                    "South Australia shows a near-fully-renewable synchronous grid in "
                    "operation, while QLD and NSW remain the largest decarbonisation and "
                    "investment headroom in the NEM."
                ),
                "description": (
                    "This chart provides a comparative breakdown of the electricity generation mix for each individual NEM state over the last 12 months. It highlights the stark regional differences in grid composition, such as South Australia's high renewable penetration versus Queensland's reliance on coal.\n\nData is based off scripts/01_fetch_nem_data.py and charted by scripts/02_generate_charts.py."
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
                "height": 600,
                "scrolling": True,
                "source": "OpenElectricity API",
                "metrics": [
                    {"label": "Retired units", "value": "43", "note": "as of last data refresh"},
                    {"label": "Operating units", "value": "44", "note": "as of last data refresh"},
                    {"label": "Retiring by 2035", "value": "12.9 GW", "note": "as of last data refresh"},
                ],
                "takeaway": (
                    "Expected coal retirements create a large, date-certain capacity gap "
                    "that must be filled by renewables and firming, making the timeline a "
                    "practical map for project development and offtake positioning."
                ),
                "description": (
                    "This timeline plots the operational status and officially scheduled retirement dates for every coal-fired power unit in the NEM. It visualizes the impending base-load capacity gap that must be replaced by new renewable generation and dispatchable firming assets.\n\nData is based off scripts/01_fetch_nem_data.py and charted by scripts/02_generate_charts.py."
                ),
            },
        ],
    },
    {
        "id": "1.3",
        "title": "NEM Infrastructure & Storage Mapping",
        "subtitle": "Geospatial Analysis of NEM Energy Infrastructure",
        "status": "done",
        "source": "OpenElectricity API · Wikipedia (Battery_storage_power_station) · nextdc.com · airtrunk.com · Equinix (Nominatim/OSM)",
        "figures": [
            {
                "id": "fig1_4",
                "number": 1,
                "title": "NEM Infrastructure Map: BESS, Solar & Data Centres",
                "sidebar_title": "INFRASTRUCTURE MAP",
                "subtitle": "Battery Energy Storage Systems, Solar Farms & Major Data Centre Locations",
                "html_path": "outputs/figures/fig1_4_infrastructure_map.html",
                "png_path": "outputs/figures/png/fig1_4_infrastructure_map.png",
                "source": "OpenElectricity API · Wikipedia · treasury.qld.gov.au · nextdc.com · airtrunk.com · Equinix/OSM",
                "metrics": [
                    {"label": "BESS Sites", "value": "91", "note": "NEM states only"},
                    {"label": "Solar Farms", "value": "136", "note": "Utility-scale"},
                    {"label": "Data Centres", "value": "42", "note": "NextDC, Equinix, AirTrunk, AWS, Google, Microsoft"},
                    {"label": "Coverage", "value": "NEM Only", "note": "All NEM regions (excludes WA / WEM)"},
                ],
                "takeaway": (
                    "Australia's BESS pipeline is geographically concentrated in NSW, VIC and SA "
                    "— precisely where coal retirements are most imminent. Data centres cluster "
                    "in the same eastern seaboard corridors, creating strong co-location "
                    "opportunities for on-site firming and dispatchable renewable supply."
                ),
                "description": (
                    "This interactive map overlays the locations of Existing/Proposed Battery Energy Storage Systems (BESS), "
                    "Existing Solar Panels, and major Data Centres across the NEM (National Electricity Market). BESS and solar markers are sized proportionally to "
                    "registered capacity (MW), revealing the scale hierarchy from large grid-scale "
                    "installations like Hornsdale and Victorian Big Battery down to smaller utility projects. "
                    "Data centre markers identify major hyperscaler and colocation operators "
                    "(NextDC, Equinix, AirTrunk, AWS, Microsoft, Google).\n\n"
                    "**BESS & Solar data sources:**\n"
                    "• OpenElectricity API (openelectricity.org.au) — live registered battery and solar units across all NEM regions (NSW, QLD, VIC, SA, TAS)\n"
                    "• treasury.qld.gov.au — official Queensland government plant data\n"
                    "• Wikipedia — Battery_storage_power_station article wikitables (operating, under construction & planned Australian projects)\n"
                    "• Coordinates geocoded live via Nominatim / OpenStreetMap where not embedded in source data\n\n"
                    "**Data centre sources:**\n"
                    "• nextdc.com — facility pages scraped for 12 operating Australian sites (S1–S6, M1–M3, B1–B2, C1, A1, SC1)\n"
                    "• airtrunk.com — facility pages scraped for SYD1, SYD2, SYD3, MEL1, MEL2\n"
                    "• Equinix — 12 Australian sites (SY1–SY6, ME1–ME3, BR1, AD1, CA1) geocoded via Nominatim/OSM using publicly listed suburb locations\n"
                    "• Cloud provider regions (AWS, Google Cloud, Microsoft Azure, Oracle Cloud) geocoded via Nominatim/OSM"
                ),
            },
        ],
    },
    {
        "id": "2.1",
        "title": "Electricity trading market",
        "subtitle": "Electricity Trading Market Volatility",
        "status": "done",
        "source": "OpenElectricity API / NEMOSIS (AEMO MMS Data)",
        "figures": [
            {
                "id": "fig2_1",
                "number": 1,
                "title": "Spot Price Volatility Heatmap",
                "sidebar_title": "SPOT PRICE HEATMAP",
                "subtitle": "QLD Average Spot Prices by Hour and Day (Past 365 Days)",
                "html_path": "outputs/figures/fig2_1_spot_heatmap.html",
                "png_path": "outputs/figures/png/fig2_1_spot_heatmap.png",
                "source": "OpenElectricity API",
                "metrics": [
                    {"label": "Region", "value": "QLD1", "note": "Representative NEM state"},
                    {"label": "Data window", "value": "365 days", "note": "Historical spot prices"},
                    {"label": "Interval", "value": "Hourly avg", "note": "By hour & day of week"},
                ],
                "takeaway": (
                    "Identifying peak pricing hours is essential for dispatchable storage and battery ROI."
                ),
                "description": (
                    "This heatmap visualizes the average wholesale electricity spot price (in AUD/MWh) across different hours of the day and days of the week, using QLD as a representative NEM state. The spot price is the price power generators receive for supplying electricity to the grid. The heatmap highlights periods of high demand and low supply (peak pricing) versus periods of oversupply (low or negative pricing).\n\nData is based off scripts/05_fetch_trading_data.py and charted by scripts/06_generate_trading_charts.py."
                ),
            },
            {
                "id": "fig2_2",
                "number": 2,
                "title": "Regulation FCAS Prices & Volumes",
                "sidebar_title": "REGULATION FCAS",
                "subtitle": "Continuous Frequency Correction (Regulation Raise/Lower)",
                "html_path": "outputs/figures/fig2_2_fcas_regulation.html",
                "png_path": "outputs/figures/png/fig2_2_fcas_regulation.png",
                "source": "NEMOSIS (AEMO MMS Data)",
                "metrics": [
                    {"label": "Data source", "value": "AEMO MMS", "note": "Via NEMOSIS"},
                    {"label": "Services", "value": "Reg Raise/Lower", "note": "Continuous correction"},
                ],
                "takeaway": (
                    "Battery storage has high opportunity for continuous frequency correction revenue."
                ),
                "description": (
                    "This chart visualizes the market prices and cleared volumes for Regulation Frequency Control Ancillary Services (FCAS). Regulation FCAS is a service used by the grid operator to continuously correct minor deviations in grid frequency (50Hz) caused by momentary imbalances between electricity supply and demand.\n\n"
                    "- Regulation Raise\n"
                    "- Regulation Lower\n\n"
                    "Data is based off scripts/05_fetch_trading_data.py and charted by scripts/06_generate_trading_charts.py."
                ),
            },
            {
                "id": "fig2_3",
                "number": 3,
                "title": "Contingency FCAS Market Value Breakdown",
                "sidebar_title": "CONTINGENCY FCAS",
                "subtitle": "Value of Fast (6s), Slow (60s), and Delayed (5m) responses",
                "html_path": "outputs/figures/fig2_3_fcas_contingency.html",
                "png_path": "outputs/figures/png/fig2_3_fcas_contingency.png",
                "source": "NEMOSIS (AEMO MMS Data)",
                "metrics": [
                    {"label": "Data source", "value": "AEMO MMS", "note": "Via NEMOSIS"},
                    {"label": "Services", "value": "6 types", "note": "Fast/Slow/Delayed Raise/Lower"},
                ],
                "takeaway": (
                    "Fast response services represent a significant portion of the contingency market value."
                ),
                "description": (
                    "This visualization breaks down the market value of Contingency FCAS, which are services that respond to sudden, major grid events like a generator tripping off. It shows the value split between Fast (6 seconds), Slow (60 seconds), and Delayed (5 minutes) response times, demonstrating the premium paid for rapid-response assets like batteries.\n\n"
                    "- Fast Raise: Increase generation or reduce load within 6 seconds during under-frequency events\n"
                    "- Fast Lower: Reduce generation or increase load within 6 seconds during over-frequency events\n"
                    "- Slow Raise: Stabilize low frequency within 60 seconds\n"
                    "- Slow Lower: Stabilize high frequency within 60 seconds\n"
                    "- Delayed Raise: Restore frequency within 5 minutes\n"
                    "- Delayed Lower: Restore frequency within 5 minutes\n\n"
                    "Data is based off scripts/05_fetch_trading_data.py and charted by scripts/06_generate_trading_charts.py."
                ),
            }
        ],
    },

    {
        "id": "2.2",
        "title": "Weather & Market Price Correlation",
        "subtitle": "Environmental Influence on Target Metrics",
        "status": "done",
        "source": "Open-Meteo API / OpenElectricity API",
        "figures": [
            {
                "id": "fig2_4",
                "number": 1,
                "title": "Weather & Market Price Correlation",
                "sidebar_title": "WEATHER & SPOT PRICE",
                "subtitle": "Temperature, Demand, and Solar Irradiance Impact",
                "html_path": "outputs/figures/fig2_4_weather_correlation.html",
                "png_path": "",
                "source": "Open-Meteo & OpenElectricity API",
                "height": 950,
                "metrics": [
                    {"label": "Data window", "value": "Available history", "note": "Merged hourly data"},
                    {"label": "Weather points", "value": "Temp / Solar / Wind"}
                ],
                "takeaway": (
                    "Extreme weather directly drives spot price volatility and demand surges."
                ),
                "description": (
                    "This interactive chart provides a time-series view of hourly temperature against spot prices and demand, as well as a scatter plot comparing solar irradiance with market prices. It reveals how high midday solar correlates with negative prices, and how extreme temperatures trigger price spikes.\n\nData is based off scripts/09_fetch_weather_data.py and charted by scripts/10_generate_weather_charts.py."
                ),
            }
        ]
    },
    {
        "id": "3",
        "title": "IMPACT OF AI DATA CENTER POWER DEMAND ON THE POWER GRID",
        "subtitle": "AI 資料中心用電需求對電網之衝擊",
        "status": "done",
        "source": "HDRE Research",
        "figures": [
            {
                "id": "fig3_1",
                "number": 1,
                "type": "outline",
                "title": "3. Impact of AI Data Center Power Demand on the Power Grid",
                "sidebar_title": "RESEARCH OUTLINE",
                "subtitle": "AI 資料中心用電需求對電網之衝擊",
                "html_path": "",
                "png_path": "",
                "source": "HDRE Research",
                "metrics": [],
                "takeaway": "",
                "description": (
                    "<div class='outline-container' style='border-top: 1px solid var(--line); padding-top: 24px; margin-top: 16px;'>"
                    "  <div class='outline-section' style='margin-bottom: 28px;'>"
                    "    <h3 style='color: var(--ivory); font-family: Inter, sans-serif; font-size: 18px; font-weight: 500; margin-bottom: 12px;'>3.1 Global and Local Market Analysis</h3>"
                    "  </div>"
                    "  <div class='outline-subsection' style='margin-bottom: 24px; border-left: 2px solid var(--line-strong); padding-left: 16px;'>"
                    "    <h4 style='color: var(--wind); font-family: Inter, sans-serif; font-size: 15px; font-weight: 500; margin-bottom: 6px; white-space: normal; word-wrap: break-word; line-height: 1.4;'>3.1.1 Global Data Center Development Assessment: Australia vs. International Benchmarks, Government Initiatives, Regulatory Constraints, Policy Subsidies, Key Market Players, and Strategic Opportunities for HDRE</h4>"
                    "    <p style='color: var(--muted); font-size: 14px; font-style: italic; line-height: 1.6; margin: 0;'>數據中心全球發展評估：澳洲與國際對比、政府計畫、法規限制、政策補貼、市場關鍵參與者及 HDRE 的發展機會</p>"
                    "  </div>"
                    "  <div class='outline-subsection' style='margin-bottom: 24px; border-left: 2px solid var(--line-strong); padding-left: 16px;'>"
                    "    <h4 style='color: var(--wind); font-family: Inter, sans-serif; font-size: 15px; font-weight: 500; margin-bottom: 6px; white-space: normal; word-wrap: break-word; line-height: 1.4;'>3.1.2 Projections of Power Consumption Growth and Green Energy Deficits, and Potential Business Opportunities for HDRE</h4>"
                    "    <p style='color: var(--muted); font-size: 14px; font-style: italic; line-height: 1.6; margin: 0;'>用電成長與綠電需求缺口推估及 HDRE 的潛在商機</p>"
                    "  </div>"
                    "</div>"
                ),
            },
            {
                "id": "ch3_fig1",
                "number": 2,
                "title": "Global Data Centre Capacity — Australia in Context",
                "sidebar_title": "GLOBAL COMPARISON",
                "subtitle": "Global comparison of installed data centre capacity and growth rates",
                "html_path": "outputs/figures/ch3_fig1_international_comparison.html",
                "png_path": "",
                "source": "AEMO / HDRE Research",
                "metrics": [
                    {"label": "Australia Capacity", "value": "1.3 GW"},
                    {"label": "APAC Growth Leader", "value": "25.1%"}
                ],
                "takeaway": "Australia ranks 6th globally at 1.3 GW, but leads Asia-Pacific in growth rate at 25.1%/yr — the fastest expansion trajectory in the region. NSW alone has 11.4 GW in the planning pipeline.",
                "description": "This chart compares Australia's data centre capacity against international benchmarks, highlighting its rapid growth rate within the Asia-Pacific region."
            },
            {
                "id": "ch3_fig2",
                "number": 3,
                "title": "AI Data Centre Power Demand Forecast",
                "sidebar_title": "DEMAND FORECAST",
                "subtitle": "AEMO 2026 ISP · Three scenarios · 2025–2050",
                "html_path": "outputs/figures/ch3_fig2_demand_forecast.html",
                "png_path": "",
                "source": "AEMO 2026 ISP",
                "metrics": [
                    {"label": "2030 Step Change", "value": "8.1 TWh"},
                    {"label": "NEM share 2050", "value": "11%"}
                ],
                "takeaway": "Under AEMO's Step Change scenario, data centre demand rises from 3.9 TWh (2025) to 8.1 TWh by 2030, reaching 33.3 TWh by 2050 — equivalent to roughly 11% of total NEM generation.",
                "description": "Projections of data centre power consumption in Australia across AEMO's ISP progressive, step, and green export scenarios."
            },
            {
                "id": "ch3_fig3",
                "number": 4,
                "title": "Green Energy Supply vs Data Centre Demand",
                "sidebar_title": "GREEN ENERGY GAP",
                "subtitle": "Renewable supply gap analysis · HDRE opportunity zone",
                "html_path": "outputs/figures/ch3_fig3_renewable_gap.html",
                "png_path": "",
                "source": "HDRE Research",
                "metrics": [
                    {"label": "Supply Gap 2035", "value": "55%"}
                ],
                "takeaway": "Tech giants (Microsoft, Google, OpenAI) have committed to 100% renewable power, but available renewable supply will cover only ~45% of projected DC demand by 2035, creating a structural green energy deficit — HDRE's primary market opportunity.",
                "description": "Analysis of the supply deficit between available renewable energy generation and data centre load demands."
            },
            {
                "id": "ch3_fig4",
                "number": 5,
                "title": "DC Pipeline vs Renewable Readiness by State",
                "sidebar_title": "STATE BREAKDOWN",
                "subtitle": "NEM states compared · MW pipeline vs renewable share %",
                "html_path": "outputs/figures/ch3_fig4_state_breakdown.html",
                "png_path": "",
                "source": "AEMO / HDRE Research",
                "metrics": [
                    {"label": "NSW Pipeline", "value": "12,050 MW"}
                ],
                "takeaway": "NSW dominates with 11.4 GW in the pipeline but only 38% renewable share — the largest mismatch in the NEM. QLD has low pipeline (980 MW) but rich solar resources, representing an early-mover opportunity for HDRE.",
                "description": "State-by-state comparison of operational and planned data centre capacity pipeline against local renewable energy share."
            }
        ],
    }
]
