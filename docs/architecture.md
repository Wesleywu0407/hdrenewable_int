# Architecture

The project has three runtime layers:

1. Data pipelines in `scripts/chapter_*`
2. Generated data and chart artifacts in `data/`, `runtime/`, `logs/`, and `outputs/`
3. Streamlit dashboard code in `dashboard/`

The chapter packages group the implementation by dashboard/report section:

- `scripts/chapter_1/`: Queensland renewables, NEM grid analysis, and infrastructure mapping
- `scripts/chapter_2/`: trading market volatility and weather/market correlation
- `scripts/chapter_3/`: AI data-centre demand analysis and policy/news refresh artifacts
- `scripts/common/`: shared paths, constants, cache helpers, logging, and infrastructure cleaning

The primary invocation path is `python -m scripts.chapter_x.module_name`. Shell refresh commands live inside the relevant chapter package, for example `bash scripts/chapter_1/run_nem_scrape.sh`.

The dashboard reads `dashboard/config.py` for chapter and figure metadata, embeds generated Plotly HTML for most figures, and renders the infrastructure map live via `scripts.chapter_1.generate_infrastructure_charts.build_infrastructure_map`.
