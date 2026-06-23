# Dashboard & Project Structure Plan

Here is the structural outline for the HTML Dashboard and the underlying data pipelines, including the current completion status and a brief summary of what each component is supposed to do.

## 1. UI Structure (The HTML Dashboard)

### Sidebar Navigation (Chapters)
* **1. NEM Grid & Queensland Solar**
  * 1.1 Queensland Renewable Energy Development `[Completed]`
    * *Focuses on QLD's specific energy mix and capacity pipeline, showing recent acceleration and convergence with peer states rather than stagnation. Includes the following diagrams:*
      * **Fig 1: QLD Renewable Share vs Peers** `[Completed]`: A line chart showing QLD converging with NSW.
        * *Source*: OpenElectricity `/network/fueltech/mix`
        * *Aggregation*: Monthly renewable vs non-renewable generation ratio
      * **Fig 2: QLD Fuel Mix Evolution** `[Completed]`: A stacked area chart showing generation by fuel type.
        * *Source*: OpenElectricity `/network/fueltech/mix`
        * *Aggregation*: Monthly generation sum per fuel tech over the last 24 months
      * **Fig 3: QLD Negative Spot-Price Frequency** `[Completed]`: Bar chart of monthly negative price hours.
        * *Source*: OpenElectricity `/network/pricing`
        * *Aggregation*: Hourly spot prices, counting total hours per month below $0/MWh
  * 1.2 National Electricity Market (NEM) Grid Analysis `[Completed]`
    * *Analyzes the broader NEM grid. Includes the following diagrams:*
      * **Fig 1: NEM Real-time Generation Mix** `[Completed]`: A 7-day 30-minute interval stacked area chart showing live generation by fuel type.
        * *Source*: OpenElectricity `/network/market/interval`
        * *Aggregation*: 5-min power data grouped into 30-min sums by fuel tech
      * **Fig 2: Monthly Generation by Fuel Type** `[Completed]`: A long-term area chart illustrating how zero-marginal-cost solar and wind are eroding coal's share.
        * *Source*: OpenElectricity `/network/fueltech/mix`
        * *Aggregation*: Monthly historical energy total per fuel tech
      * **Fig 3: Generation Mix by State** `[Completed]`: A stacked bar chart comparing the energy breakdown across the 5 NEM states over the last 12 months.
        * *Source*: OpenElectricity `/network/fueltech/mix`
        * *Aggregation*: Sum of latest 12 months energy grouped by state and fuel tech
      * **Fig 4: Coal Retirement Timeline** `[Completed]`: A Gantt chart mapping out the operating lifespan and planned closure dates for NEM coal units.
        * *Source*: OpenElectricity `/facilities`
        * *Aggregation*: Commenced and expected closure dates to map operating lifespans
* **2. Electricity Trading Market Volatility**
  * 2.1 Spot Market (Power Supply) `[Not Started]`
    * *Tracks hourly/daily price volatility to identify lucrative trading windows. Includes potential diagrams:*
      * **Fig: Spot Price Volatility Heatmap**: A daily/hourly heatmap to identify the most lucrative trading windows.
        * *Source*: OpenElectricity `/network/pricing`
        * *Aggregation*: 5-minute spot prices averaged into hourly buckets across days
  * 2.2 Regulation FCAS `[Not Started]`
    * *Monitors continuous frequency correction markets (Raise/Lower) to gauge battery storage opportunities. Includes potential diagrams:*
      * **Fig: Regulation FCAS Prices & Volumes**: Line charts tracking the cost and volume of continuous frequency correction (Regulation Raise/Lower).
        * *Source*: OpenElectricity FCAS endpoints
        * *Aggregation*: 5-minute pricing and enabled volumes averaged daily/monthly
  * 2.3 Contingency FCAS `[Not Started]`
    * *Analyzes fast, slow, and delayed frequency response markets triggered by grid disruptions. Includes potential diagrams:*
      * **Fig: Contingency FCAS Market Value Breakdown**: Stacked bar chart comparing the value of Fast (6s), Slow (60s), and Delayed (5m) responses.
        * *Source*: OpenElectricity FCAS endpoints
        * *Aggregation*: Total market value derived from price × volume over the reporting period
* **3. AI Data Center Power Demand**
  * 3.1 Global Data Center Development Assessment `[Not Started]`
    * *Compares Australian data center growth against global benchmarks and policies.*
  * 3.2 Projections & Green Energy Deficits `[Not Started]`
    * *Forecasts the impending power supply gap caused by AI demand, highlighting HDRE business opportunities. Includes potential diagrams:*
      * **Fig: Projected AI Energy Demand vs Renewable Supply**: An area chart forecasting the impending power supply gap (Green Energy Deficit) to highlight business opportunities for HDRE.
        * *Source*: AEMO ISP & Global Industry Reports
        * *Aggregation*: Overlaying long-term renewable supply forecasts with extrapolated data center demand

### Main Dashboard Layout
* **Header / Topbar** `[Completed]`
  * *Displays the project title, data source, and when the data was last refreshed.*
* **Hero Visualization Area** `[Completed]`
  * *The primary interactive chart stage (e.g., stacked area charts for real-time generation) for the currently selected chapter.*
* **Key Metric Tiles (KPIs)** `[Completed]`
  * *Quick-glance statistic blocks (e.g., Coal baseload %, Solar peak GW) located below the main chart to summarize the data.*
* **Research Notes & Takeaways** `[Completed]`
  * *Stylized text callouts providing qualitative analysis, conclusions, and strategic opportunities for HDRE based on the chart.*

---

## 2. Data Pipeline Structure (Python Scripts)

To power the dashboard above, the data ingestion and chart generation pipeline is structured as follows:

### Setup & Utilities
* `scripts/00_test_api.py` `[Completed]`
  * *Validates the OpenElectricity API key setup and ensures the python environment can connect to the data endpoints.*

### Chapter 1: NEM & QLD Grid Analysis
* `scripts/01_fetch_nem_data.py` `[Completed]`
  * *Pulls all broad NEM grid data (7-day real-time mix, annual mix, coal timelines) from the OpenElectricity API into Parquet files.*
* `scripts/02_generate_charts.py` `[Completed]`
  * *Converts the fetched NEM Parquet data into standalone, interactive Plotly HTML charts.*
* `scripts/03_fetch_qld_data.py` `[Completed]`
  * *Pulls QLD-specific facility capacity, historical additions, and spot price data into CSV files.*
* `scripts/04_generate_qld_charts.py` `[Completed]`
  * *Converts the fetched QLD CSV data into standalone, interactive Plotly HTML charts.*

### Chapter 2: Electricity Trading Market Volatility
* `scripts/05_fetch_trading_data.py` `[Not Started]`
  * *Will pull NEM spot market price history and FCAS market (Regulation and Contingency) volumes and pricing.*
* `scripts/06_generate_trading_charts.py` `[Not Started]`
  * *Will generate visual heatmaps or line charts showing price volatility spikes and FCAS market trends.*

### Chapter 3: AI Data Center Power Demand
* `scripts/07_fetch_ai_demand.py` `[Not Started]`
  * *Will ingest AI demand projections, scrape global benchmark reports, or load static energy deficit models.*
* `scripts/08_generate_ai_charts.py` `[Not Started]`
  * *Will visualize the gap between current renewable supply trajectories and future AI data center energy needs.*

---

## 3. Technical Migration Tasks

If moving away from Streamlit to a true native HTML/JS/CSS app:
* **Initialize Vite/React web application** `[Not Started]`
  * *Sets up a fast, modern frontend framework to host the dashboard.*
* **Set up premium Vanilla CSS design system** `[Not Started]`
  * *Implements the strict dark mode UI, glassmorphism, and micro-animations to create a premium "research terminal" feel.*
* **Convert Python HTML chart exports to JSON data exports** `[Not Started]`
  * *Changes the Python pipeline to output raw JSON data instead of static HTML files, allowing the frontend to control rendering.*
* **Implement native frontend charting** `[Not Started]`
  * *Uses a JavaScript library (like Recharts or Plotly.js) to draw the charts natively in the browser using the JSON data.*

---

## 4. Architectural Notes

### 4.1 Data Resolution and the 7-Day Window
The dashboard's real-time charts specifically pull data over a **7-day rolling window**. The primary reason for this constraint is to ensure the ingestion of **5-minute interval data**.

* **NEM Market Mechanics:** As of October 1, 2021, the Australian Energy Market Operator (AEMO) transitioned the National Electricity Market (NEM) to a **Five Minute Settlement (5MS)** rule, matching the physical 5-minute dispatch process.
* **OpenElectricity API Constraints:** The OpenElectricity API provides data at this native 5-minute resolution for short-term queries (like the past 7 days). For longer historical queries (e.g., months or years), the API often aggregates the data into 30-minute, hourly, or daily intervals to optimize payload sizes and API performance.
* **Pipeline Strategy:** By restricting the real-time fetch window to 7 days, the pipeline guarantees access to the high-fidelity 5-minute data necessary to accurately capture rapid spot market volatility, FCAS spikes, and generation dispatch patterns.
