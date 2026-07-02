# Data Pipeline

## Chapter 1

`scripts.chapter_1.fetch_nem_data` fetches OpenElectricity NEM/WEM power, emissions, price, fuel-mix, renewable-share, and coal-facility datasets into `data/raw/`.

`scripts.chapter_1.fetch_qld_data` derives Queensland-specific facility, capacity-history, peer-addition, fuel-mix, and spot-price datasets from OpenElectricity.

`scripts.chapter_1.fetch_infrastructure_data` scrapes and merges BESS, solar, and data-centre locations. State normalization is owned by `scripts.common.infrastructure` and is applied before CSVs are saved.

Chart modules in `scripts.chapter_1` render the generated datasets into `outputs/figures/`.

## Chapter 2

`scripts.chapter_2.fetch_trading_data` pulls FCAS source tables through nemosis and writes trading datasets to `data/raw/`.

`scripts.chapter_2.fetch_weather_data` fetches historical weather data and merges it with QLD market/demand data.

Chart modules in `scripts.chapter_2` render trading and weather figures into `outputs/figures/`.

## Chapter 3

`scripts.chapter_3.generate_ch3_charts` builds the Chapter 3 analysis charts from processed and raw data.

`scripts.chapter_3.ch3_refresh_pipeline` writes policy/news refresh artifacts to `runtime/ch3/` and `logs/`.

## Shared Behavior

`scripts.common.api` provides cache freshness checks, timestamped logging setup, CSV merge helpers, and cache-or-fetch behavior.

`scripts.common.constants` centralizes NEM regions, fueltech column mappings, chart palettes, and timezone constants.

Generated data paths remain stable for the dashboard and export tooling: raw CSVs stay in `data/raw/`, generated figures stay in `outputs/figures/`, and refresh status/log artifacts stay in `runtime/` and `logs/`.
