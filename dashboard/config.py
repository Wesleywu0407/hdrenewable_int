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
                    {"label": "QLD Renewable Share", "value": "32.0%"},
                    {"label": "NSW Renewable Share", "value": "30.9%"}
                ],
                "takeaway": (
                    "Queensland has accelerated its renewable deployment significantly, increasing its renewable generation share from 26.5% to 32.0% over the last 24 months. This rapid growth has allowed Queensland to slightly overtake its peer state New South Wales (30.9% as of June 2026)."
                ),
                "description": (
                    "This graph compares the percentage of total electricity generated from renewable sources (solar, wind, hydro, bioenergy) in Queensland against New South Wales over time. It illustrates the relative pace at which these two major states are transitioning away from fossil fuels.\n\nData is based off scripts/03_fetch_qld_data.py (which uses the openelectricity Python SDK to pull live timeseries datasets via the OpenElectricity API) and charted by scripts/04_generate_qld_charts.py."
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
                    {"label": "Coal Share", "value": "Down to 55.3%"},
                    {"label": "Wind Share", "value": "Up to 11.1%"},
                    {"label": "Total Renewables", "value": "32.0%"}
                ],
                "takeaway": (
                    "Over the past 24 months, Queensland's reliance on coal generation has noticeably decreased from 62.6% to 55.3%. This base-load capacity gap has been filled primarily by a remarkable doubling in wind generation (growing from 5.2% to 11.1%), which has steadily driven the total renewable penetration up to 32.0%."
                ),
                "description": (
                    "This area chart visualizes the total volume of electricity generated in Queensland by different fuel types (coal, gas, solar, wind, etc.) over the past 24 months. It highlights the changing proportions and seasonal variations of each generation source.\n\nData is based off scripts/03_fetch_qld_data.py (which uses the openelectricity Python SDK to pull live timeseries datasets via the OpenElectricity API) and charted by scripts/04_generate_qld_charts.py."
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
                    {"label": "Negative Prices", "value": "Frequent"},
                    {"label": "Recent 6-Month Avg", "value": "~59 hrs/month"},
                    {"label": "Historical Peak", "value": ">170 hrs/month"}
                ],
                "takeaway": (
                    "Queensland experiences a high frequency of negative wholesale spot prices, occasionally peaking at over 170 hours per month during high-solar seasons. These frequent negative price events indicate severe daytime oversupply, presenting a highly lucrative arbitrage and firming opportunity for battery storage operators."
                ),
                "description": (
                    "This bar chart tracks the frequency of negative wholesale electricity spot prices in Queensland. A negative spot price occurs when the supply of electricity exceeds demand, often during periods of high solar generation, meaning generators effectively pay the market to take their power.\n\nData is based off scripts/03_fetch_qld_data.py (which uses the openelectricity Python SDK to pull live timeseries datasets via the OpenElectricity API) and charted by scripts/04_generate_qld_charts.py."
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
                    "This interactive chart stacks the real-time electricity generation from all fuel types across the National Electricity Market (NEM) to show total demand over the past 7 days. The overlaid dashed line represents the wholesale electricity spot price (in AUD/MWh) during those same intervals.\n\nData is based off scripts/01_fetch_nem_data.py (which queries the OpenElectricity API using the openelectricity Python SDK for NEM-wide generation data) and charted by scripts/02_generate_charts.py."
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
                    {"label": "Coal Share", "value": "Down to 51.5%", "note": "From 56.9% in Jul 2024"},
                    {"label": "Wind Share", "value": "Up to 17.7%", "note": "From 15.2% in Jul 2024"},
                    {"label": "Solar Share", "value": "12.7%", "note": "Subject to seasonal dips"},
                ],
                "takeaway": (
                    "Across the NEM, the 24-month window from July 2024 to June 2026 shows a decisive structural shift. Coal's contribution to the monthly generation mix eroded substantially from 56.9% to 51.5%, displaced by consistent growth in wind generation (which expanded from 15.2% to 17.7%) and persistent, zero-marginal-cost solar generation."
                ),
                "description": (
                    "This stacked bar chart aggregates the total monthly electricity generation across all NEM regions, broken down by fuel type. It reveals how seasonal weather patterns (affecting solar and wind output) and long-term trends shape the overall grid energy mix.\n\nData is based off scripts/01_fetch_nem_data.py (which queries the OpenElectricity API using the openelectricity Python SDK for NEM-wide generation data) and charted by scripts/02_generate_charts.py."
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
                    {"label": "QLD Renewables", "value": "34.5%", "note": "56.5% Coal"},
                    {"label": "NSW Renewables", "value": "39.4%", "note": "56.0% Coal"},
                    {"label": "SA Renewables", "value": "76.6%", "note": "0% Coal"},
                ],
                "takeaway": (
                    "Analyzing the last 12 months reveals starkly different grid realities. South Australia operates a world-leading 76.6% renewable grid with zero coal. In contrast, the eastern seaboard heavyweights—QLD and NSW—still rely on coal for over 56% of their energy, representing massive upside and investment headroom for renewable infrastructure."
                ),
                "description": (
                    "This chart provides a comparative breakdown of the electricity generation mix for each individual NEM state over the last 12 months. It highlights the stark regional differences in grid composition, such as South Australia's high renewable penetration versus Queensland's reliance on coal.\n\nData is based off scripts/01_fetch_nem_data.py (which queries the OpenElectricity API using the openelectricity Python SDK for NEM-wide generation data) and charted by scripts/02_generate_charts.py."
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
                    {"label": "Retired units", "value": "43"},
                    {"label": "Operating units", "value": "44"},
                    {"label": "Retiring by 2035", "value": "13.6 GW", "note": "Of 21.1 GW total"},
                ],
                "takeaway": (
                    "The NEM is approaching a massive, date-certain thermal cliff. Of the 21.1 GW of currently operating coal capacity across 44 units, a staggering 13.6 GW (over 64%) is officially scheduled to retire by 2035. This timeline acts as an aggressive, unalterable deadline that mandates the rapid acceleration of replacement renewable and firming capacity."
                ),
                "description": (
                    "This timeline plots the operational status and officially scheduled retirement dates for every coal-fired power unit in the NEM. It visualizes the impending base-load capacity gap that must be replaced by new renewable generation and dispatchable firming assets.\n\nData is based off scripts/01_fetch_nem_data.py (which queries the OpenElectricity API using the openelectricity Python SDK for NEM-wide generation data) and charted by scripts/02_generate_charts.py."
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
                "source": "OpenElectricity API · Wikipedia · treasury.qld.gov.au · HDRE/ZEBRE Verified Data · AEMO 2024 ISP · VicGrid · EnergyCo NSW · Geoscience Australia",
                "metrics": [
                    {"label": "BESS Sites", "value": "191", "note": "QLD (101) & NSW (29) leading"},
                    {"label": "BESS Capacity", "value": "68,731 MW", "note": "Existing & proposed"},
                    {"label": "Solar Farms", "value": "275", "note": "Utility-scale"},
                    {"label": "Solar Capacity", "value": "33,013 MW", "note": "Utility-scale"},
                    {"label": "Data Centres", "value": "48", "note": "NSW (21) & VIC (13) leading"},
                    {"label": "Renewable Energy Zones", "value": "56", "note": "Across 4 mapped layers"},
                    {"label": "Transmission Lines", "value": "2,000", "note": "Segments across NEM"},
                ],
                "takeaway": (
                    "The spatial analysis uncovers a critical geographic mismatch between future generation and incoming load:\n\n"
                    "• **Renewable Supply is Northern-Weighted:** A massive pipeline of 191 BESS sites (68.7 GW) and 275 utility solar farms (33.0 GW) is heavily concentrated in Queensland and NSW.\n"
                    "• **Data Centre Load is Southern-Weighted:** The 48 major energy-intensive AI and data centres are clustered primarily around NSW (21) and Victoria (13).\n\n"
                    "This regional separation between generation and consumption underscores the urgent need for the **56 Renewable Energy Zones** and **2,000 major transmission segments** to effectively bridge the power gap."
                ),
                "description": (
                    "This interactive map overlays the locations of Existing/Proposed Battery Energy Storage Systems (BESS), "
                    "Existing Solar Panels, Renewable Energy Zones (REZs), and major Data Centres across the NEM (National Electricity Market). "
                    "BESS and solar markers are sized proportionally to registered capacity (MW), revealing the scale hierarchy from large grid-scale "
                    "installations like Hornsdale and Victorian Big Battery down to smaller utility projects. "
                    "Data centre markers identify major hyperscaler and colocation operators "
                    "(NextDC, Equinix, AirTrunk, AWS, Microsoft, Google). REZ polygons outline the optimal geographic regions identified "
                    "for future renewable generation and transmission infrastructure.\n\n"
                    "**BESS & Solar data sources:**\n"
                    "• OpenElectricity API (openelectricity.org.au) - live registered battery and solar units across all NEM regions (NSW, QLD, VIC, SA, TAS)\n"
                    "• treasury.qld.gov.au - official Queensland government plant data\n"
                    "• Wikipedia - Battery_storage_power_station article wikitables (operating, under construction & planned Australian projects)\n"
                    "• HDRE/ZEBRE Verified Data: Manual insertion of known JV projects missing from public databases\n"
                    "• Coordinates geocoded live via Nominatim / OpenStreetMap where not embedded in source data\n\n"
                    "**Data centre sources:**\n"
                    "• nextdc.com - facility pages scraped for 12 operating Australian sites (S1-S6, M1-M3, B1-B2, C1, A1, SC1)\n"
                    "• airtrunk.com - facility pages scraped for SYD1, SYD2, SYD3, MEL1, MEL2\n"
                    "• Equinix - 12 Australian sites (SY1-SY6, ME1-ME3, BR1, AD1, CA1) geocoded via Nominatim/OSM using publicly listed suburb locations\n"
                    "• Cloud provider regions (AWS, Google Cloud, Microsoft Azure, Oracle Cloud) geocoded via Nominatim/OSM\n\n"
                    "**Renewable Energy Zone (REZ) sources:**\n"
                    "• AEMO 2024 Integrated System Plan (ISP) - Indicative onshore REZ boundaries for Queensland (9) and South Australia (9)\n"
                    "• EnergyCo NSW - Declared REZ boundaries for New South Wales (5)\n"
                    "• VicGrid - Declared REZ boundaries for Victoria (5)\n"
                    "• Department of State Growth TAS - REZ boundaries for Tasmania (3)\n\n"
                    "**Transmission Line sources:**\n"
                    "• Geoscience Australia - National Electricity Infrastructure dataset (Electricity Transmission Lines >= 220kV)\n\n"
                    "Data is based off scripts/07_fetch_infrastructure_data.py and charted by scripts/08_generate_infrastructure_charts.py."
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
                    {"label": "Peak Window", "value": "17:00-19:00", "note": "Avg ~$122/MWh"},
                    {"label": "Cheapest Window", "value": "10:00-12:00", "note": "Avg ~$9.8/MWh"},
                    {"label": "Daily Spread", "value": ">$110/MWh", "note": "Arbitrage potential"}
                ],
                "takeaway": (
                    "The spot market exhibits a massive, predictable intraday spread. Prices collapse to near-zero (averaging below $10/MWh) between 10:00 and 12:00 due to solar abundance, but skyrocket during the evening peak (17:00-19:00) to an average of over $120/MWh. This >$110/MWh daily spread forms the lucrative foundation of the battery arbitrage business case."
                ),
                "description": (
                    "This heatmap visualizes the average wholesale electricity spot price (in AUD/MWh) across different hours of the day and days of the week, using QLD as a representative NEM state. The spot price is the price power generators receive for supplying electricity to the grid. The heatmap highlights periods of high demand and low supply (peak pricing) versus periods of oversupply (low or negative pricing).\n\nData is based off scripts/05_fetch_trading_data.py (which uses the nemosis Python library to dynamically compile raw AEMO MMS SQLite tables into a local cache) and charted by scripts/06_generate_trading_charts.py."
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
                    {"label": "Avg Raise Price", "value": "$8.01/MWh"},
                    {"label": "Avg Lower Price", "value": "$3.44/MWh"},
                    {"label": "Average Volume", "value": "~47.7 MW", "note": "Cleared per interval"}
                ],
                "takeaway": (
                    "In the continuous frequency correction market (Regulation FCAS), Raise services command a significant structural premium, averaging $8.01/MWh compared to just $3.44/MWh for Lower services. This highlights the grid's constant need for dispatchable injection to stabilize momentary frequency dips, a service batteries are uniquely positioned to provide."
                ),
                "description": (
                    "This chart visualizes the market prices and cleared volumes for Regulation Frequency Control Ancillary Services (FCAS). Regulation FCAS is a service used by the grid operator to continuously correct minor deviations in grid frequency (50Hz) caused by momentary imbalances between electricity supply and demand.\n\n"
                    "- Regulation Raise\n"
                    "- Regulation Lower\n\n"
                    "Data is based off scripts/05_fetch_trading_data.py (which uses the nemosis Python library to dynamically compile raw AEMO MMS SQLite tables into a local cache) and charted by scripts/06_generate_trading_charts.py."
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
                    {"label": "Fast (6s) Share", "value": "74.2%", "note": "Of total market value"},
                    {"label": "Slow (60s) Share", "value": "23.1%"},
                    {"label": "Delayed (5m) Share", "value": "2.7%"}
                ],
                "takeaway": (
                    "Contingency FCAS market value is overwhelmingly concentrated in ultra-fast response times. Fast (6-second) response services capture 74.2% of the total market value, heavily favoring inverter-based technologies like battery storage that can respond instantaneously over slower, mechanical thermal plants."
                ),
                "description": (
                    "This visualization breaks down the market value of Contingency FCAS, which are services that respond to sudden, major grid events like a generator tripping off. It shows the value split between Fast (6 seconds), Slow (60 seconds), and Delayed (5 minutes) response times, demonstrating the premium paid for rapid-response assets like batteries.\n\n"
                    "- Fast Raise: Increase generation or reduce load within 6 seconds during under-frequency events\n"
                    "- Fast Lower: Reduce generation or increase load within 6 seconds during over-frequency events\n"
                    "- Slow Raise: Stabilize low frequency within 60 seconds\n"
                    "- Slow Lower: Stabilize high frequency within 60 seconds\n"
                    "- Delayed Raise: Restore frequency within 5 minutes\n"
                    "- Delayed Lower: Restore frequency within 5 minutes\n\n"
                    "Data is based off scripts/05_fetch_trading_data.py (which uses the nemosis Python library to dynamically compile raw AEMO MMS SQLite tables into a local cache) and charted by scripts/06_generate_trading_charts.py."
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
                    {"label": "Extreme Cold Avg", "value": "$92.66/MWh", "note": "vs $34.51 in Extreme Heat"},
                    {"label": "Top 10% Demand", "value": "$124.39/MWh", "note": "When >7,729 MW"},
                    {"label": "Max Price Event", "value": "$1,924.53/MWh", "note": "Low solar (147 W/m²) & Peak demand"}
                ],
                "takeaway": (
                    "Weather dictates severe market extremes with strong statistical correlation. Solar irradiance holds a strong negative correlation (-0.55) with price, driving massive negative price events (e.g., -$199/MWh during 659 W/m² irradiance and low demand). Conversely, extreme cold (<13.3°C) drives average prices almost 3x higher than extreme heat ($92 vs $34) due to winter evening peaks lacking solar cover. When demand enters the top 10th percentile (>7,729 MW), prices average an exceptionally lucrative $124.39/MWh."
                ),
                "description": (
                    "This interactive chart provides a time-series view of hourly temperature against spot prices and demand, as well as a scatter plot comparing solar irradiance with market prices. It reveals how high midday solar correlates with negative prices, and how extreme temperatures trigger price spikes.\n\nData is based off scripts/09_fetch_weather_data.py (which issues HTTP GET requests to the Open-Meteo API for historical weather data based on specific coordinates) and charted by scripts/10_generate_weather_charts.py."
                ),
            }
        ]
    },
    {
        "id": "3",
        "title": "DATA CENTRE LOAD VS. FIRMING CAPACITY",
        "subtitle": "Geographical Mismatch & The BESS Arbitrage Opportunity",
        "status": "done",
        "source": "AEMO / OpenElectricity API / Open-Meteo",
        "figures": [
            {
                "id": "fig3_1",
                "number": 1,
                "type": "outline",
                "title": "3. Geographic Load vs. Generation Mismatch",
                "sidebar_title": "RESEARCH OUTLINE",
                "subtitle": "Empirical analysis of load vs. generation",
                "html_path": "",
                "png_path": "",
                "source": "AEMO / OpenElectricity API",
                "metrics": [],
                "takeaway": "",
                "description": (
                    "<div class='outline-container' style='border-top: 1px solid var(--line); padding-top: 24px; margin-top: 16px;'>"
                    "  <div class='outline-section' style='margin-bottom: 28px;'>"
                    "    <h3 style='color: var(--ivory); font-family: Inter, sans-serif; font-size: 18px; font-weight: 500; margin-bottom: 12px;'>3.1 Geographic Load vs. Generation Mismatch</h3>"
                    "  </div>"
                    "  <div class='outline-subsection' style='margin-bottom: 24px; border-left: 2px solid var(--line-strong); padding-left: 16px;'>"
                    "    <h4 style='color: var(--wind); font-family: Inter, sans-serif; font-size: 15px; font-weight: 500; margin-bottom: 6px; white-space: normal; word-wrap: break-word; line-height: 1.4;'>Southern Load, Northern Generation</h4>"
                    "    <p style='color: var(--muted); font-size: 14px; font-style: italic; line-height: 1.6; margin: 0;'>Data centres are highly concentrated in NSW and VIC, while the majority of BESS and solar development is occurring in QLD and NSW, creating a structural reliance on interstate transmission.</p>"
                    "  </div>"
                    "  <div class='outline-subsection' style='margin-bottom: 24px; border-left: 2px solid var(--line-strong); padding-left: 16px;'>"
                    "    <h4 style='color: var(--wind); font-family: Inter, sans-serif; font-size: 15px; font-weight: 500; margin-bottom: 6px; white-space: normal; word-wrap: break-word; line-height: 1.4;'>The BESS Arbitrage Case</h4>"
                    "    <p style='color: var(--muted); font-size: 14px; font-style: italic; line-height: 1.6; margin: 0;'>Running data centres 24/7 on raw grid spot prices exposes operators to massive evening peak costs. Using BESS to firm this power unlocks significant arbitrage value.</p>"
                    "  </div>"
                    "</div>"
                ),
            },
            {
                "id": "ch3_fig1",
                "number": 2,
                "title": "State-by-State Mismatch",
                "sidebar_title": "GEOGRAPHIC MISMATCH",
                "subtitle": "Data Centre Load vs Renewable Firming Capacity",
                "html_path": "outputs/figures/ch3_fig1_state_mismatch.html",
                "png_path": "",
                "source": "OpenElectricity API / Data Centre Data",
                "metrics": [
                    {"label": "NSW & VIC Data Centres", "value": "34 of 48", "note": "71% of total"},
                    {"label": "QLD BESS & Solar", "value": "42.3 GW", "note": "62% of NEM capacity"}
                ],
                "takeaway": "There is a severe geographic mismatch. 71% of major data centres (34 out of 48) are clustered in Southern states (NSW and VIC). Conversely, over 62% of upcoming BESS and solar firming capacity is located in Queensland. This Southern Load vs Northern Generation dynamic requires immense transmission routing and localized firming solutions.",
                "description": "This chart highlights the imbalance between where major data centres are built and where massive renewable generation and battery storage projects are deployed.\n\nData is processed from empirical dataset CSVs."
            },
            {
                "id": "ch3_fig2",
                "number": 3,
                "title": "Hourly Spot Price & Negative Pricing Frequency",
                "sidebar_title": "PRICE VOLATILITY",
                "subtitle": "Predictable intraday pricing swings",
                "html_path": "outputs/figures/ch3_fig2_hourly_profile.html",
                "png_path": "",
                "source": "Open-Meteo & OpenElectricity API",
                "metrics": [
                    {"label": "Negative Price Frequency", "value": "16.2%"},
                    {"label": "Max Extreme", "value": "$1,924.53/MWh"}
                ],
                "takeaway": "The NEM exhibits extreme intraday price volatility. Negative pricing occurs in 16.2% of all hours due to midday solar oversupply. During evening peaks, prices can skyrocket to almost $2,000/MWh. This high volatility severely punishes baseload consumers like data centres while heavily rewarding dispatchable BESS assets.",
                "description": "Hourly average spot prices overlayed with the frequency of negative price events, demonstrating the midday slump and evening spike.\n\nData is processed from real weather and price CSVs."
            },
            {
                "id": "ch3_fig3",
                "number": 4,
                "title": "The Duck Curve: Solar vs Demand",
                "sidebar_title": "SOLAR & DEMAND",
                "subtitle": "Irradiance driving the market",
                "html_path": "outputs/figures/ch3_fig3_duck_curve.html",
                "png_path": "",
                "source": "Open-Meteo & OpenElectricity API",
                "metrics": [
                    {"label": "Midday Irradiance", "value": "High", "note": "Drives prices below zero"}
                ],
                "takeaway": "Solar generation predictably pushes midday demand and prices into negative territory, while evening demand remains high when solar drops off. This perfectly creates the 'Duck Curve' phenomenon, cementing the need for overnight BESS firming for 24/7 data centre operations.",
                "description": "Comparing average hourly solar irradiance against grid demand. High midday irradiance correlates directly with negative pricing events.\n\nData is processed from empirical datasets."
            },
            {
                "id": "ch3_fig4",
                "number": 5,
                "title": "The Value of Firming: Unfirmed Grid vs BESS Offset",
                "sidebar_title": "BESS ARBITRAGE",
                "subtitle": "Simulated Cost for 100MW Continuous Load",
                "html_path": "outputs/figures/ch3_fig4_firming_value.html",
                "png_path": "",
                "source": "Empirical Simulation",
                "metrics": [
                    {"label": "Daily Spread", "value": "Extreme"},
                    {"label": "BESS Opportunity", "value": "Arbitrage Savings"}
                ],
                "takeaway": "Simulating a 100MW constant data centre load reveals that pulling raw 24/7 power from the spot market is prohibitively expensive due to evening peaks. Utilizing a co-located or contracted BESS to charge during negative midday prices and discharge during evening peaks drastically reduces the net cost of power, proving the financial necessity of firming for AI workloads.",
                "description": "A cumulative cost comparison showing the financial impact of running a 100MW data centre purely on grid spot prices versus offsetting those costs with an optimized BESS arbitrage strategy.\n\nData is simulated from historical hourly profiles."
            }
        ],
    }
]
