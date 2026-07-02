# Deployment

## Local Production-Like Run

1. Create `.env` with `OPENELECTRICITY_API_KEY`.
2. Run `./run.sh --fetch --generate`.
3. Run `./run.sh --dashboard`.

Dependencies are locked in `requirements.txt`; `run.sh` installs from that file.

## Streamlit Host

Use `dashboard/app.py` as the app entrypoint and install from `requirements.txt`. Ensure generated files under `data/raw/`, `outputs/figures/`, `runtime/`, and `logs/` are present if the host should serve cached artifacts without running scrapers.

## Static HTML Export

Run:

```bash
./export.sh
```

The exporter lives at `tools/export_stlite.py` and recursively bundles dashboard modules, chapter packages, selected raw data, logs, runtime status, and generated figures into `dashboard_exported.html`.

## Scheduled Refresh

For cron or another scheduler, call chapter runners directly:

```bash
bash scripts/chapter_1/run_nem_scrape.sh
bash scripts/chapter_1/run_infrastructure_scrape.sh
bash scripts/chapter_2/run_weather_scrape.sh
```

Pipeline logs are timestamped. For alerting, wrap scheduled commands with your platform's notification mechanism and trigger an email or webhook when the command exits non-zero.
