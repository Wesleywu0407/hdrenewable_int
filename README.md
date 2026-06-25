# HDRE Australia NEM Grid Research Dashboard

## Quick Start (Run instantly with cached data)

To start the Streamlit dashboard immediately using pre-cached datasets:
```bash
./run.sh --dashboard
```

## Running the Complete Pipeline

To fetch fresh data and regenerate charts, configure your API credentials:

1. **Create `.env` file**:
   Create a `.env` file in the project root containing your API key:
   ```env
   OPENELECTRICITY_API_KEY=your_actual_api_key_here
   ```
   Get a free API key at [OpenElectricity Platform](https://platform.openelectricity.org.au/).

2. **Run setup, fetch, generate, and start dashboard**:
   ```bash
   ./run.sh
   ```

## CLI Reference

* **Run dashboard only (cached mode)**:
  ```bash
  ./run.sh --dashboard
  ```

* **Run data pipeline only (fetch & generate charts)**:
  ```bash
  ./run.sh --fetch --generate
  ```

* **Check all options**:
  ```bash
  ./run.sh --help
  ```

## Chapter 1.3 — Infrastructure & Storage Mapping

To re-scrape BESS and Datacentre data and regenerate the infrastructure map independently:

```bash
bash scripts/run_infrastructure_scrape.sh
```

Or via the main pipeline flag:

```bash
./run.sh --infrastructure
```

**What this does:**
1. Fetches BESS locations from the OpenElectricity API (battery units across all NEM regions) and enriches with Wikipedia's energy storage project list
2. Scrapes Australian Datacentre locations from Baxtel and datacentermap.com
3. Geocodes sites using known coordinate lookups and state centroids as fallback
4. Saves `data/raw/bess_locations.csv` and `data/raw/datacentre_locations.csv`
5. Generates `outputs/figures/fig1_4_infrastructure_map.html` — an interactive Plotly map of Australia

> **Note:** An `OPENELECTRICITY_API_KEY` in `.env` enhances BESS data quality but is not required — the pipeline falls back to Wikipedia and curated public project records.

## Chapter 2.2 — Weather & Market Price Correlation

To re-scrape weather data and regenerate the correlation charts independently:

```bash
bash scripts/run_weather_scrape.sh
```

**What this does:**
1. Fetches historical weather data (temperature, solar irradiance, wind speed) from the free Open-Meteo API.
2. Merges weather data with OpenElectricity spot price and demand data.
3. Saves `data/raw/weather_price_correlation.csv`.
4. Generates `outputs/figures/fig2_4_weather_correlation.html` — interactive Plotly charts overlaying temperature, demand, spot price, and solar irradiance correlation.
