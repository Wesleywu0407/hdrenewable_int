# HDRE NEM Research — Chapter 1.2: National Electricity Market (NEM) Grid Analysis

Data pipeline and visualization workflow for HDRE Taiwan's research report on Australia's
electricity market. This chapter produces **5 interactive charts + bilingual analytical
commentary** explaining the structure and evolution of Australia's NEM grid over the past 5 years.

## Deliverables

| # | File | Description |
|---|------|-------------|
| Fig 1 | `outputs/figures/fig1_nem_realtime_mix.html` | NEM real-time generation mix (past 7 days, 30-min) |
| Fig 2 | `outputs/figures/fig2_annual_generation_by_fuel.html` | Annual generation by fuel, 2020–2025 |
| Fig 3 | `outputs/figures/fig3_state_comparison.html` | Cross-state generation mix comparison |
| Fig 4 | `outputs/figures/fig4_renewable_share_evolution.html` | Renewable share (%) over time, per state |
| Fig 5 | `outputs/figures/fig5_coal_retirement_timeline.html` | Coal plant retirement Gantt timeline |
| — | `outputs/commentary_chapter_1_2.md` | Bilingual (EN + 繁中) analytical commentary |

## Setup

```bash
cd HDRE_NEM_Research
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Configure API key
cp .env.example .env
# edit .env and paste your OpenElectricity API key
```

Get an API key at https://platform.openelectricity.org.au/

## Usage

```bash
python scripts/00_test_api.py        # verify connectivity
python scripts/01_fetch_nem_data.py  # fetch + cache all datasets to data/raw/
python scripts/02_generate_charts.py # build the 5 HTML charts
```

## Data source

OpenElectricity API — https://openelectricity.org.au/ (docs: https://docs.openelectricity.org.au/)

## Project layout

```
HDRE_NEM_Research/
├── .env                  # API key (gitignored — never commit)
├── data/raw/             # cached raw API responses (Parquet)
├── data/processed/       # cleaned data ready for plotting
├── scripts/              # 00_test_api, 01_fetch, 02_generate_charts
├── notebooks/            # free-form exploration
├── outputs/figures/      # generated HTML charts
└── dashboard/            # placeholder for later Streamlit phase
```
