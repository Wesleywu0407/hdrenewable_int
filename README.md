# HDRE Australia NEM Grid Research Dashboard

## Prerequisites

If you are setting this up on a fresh computer, ensure you have the following installed:
- **Python 3** (with `pip` and `venv` or `virtualenv` available)
  - *Ubuntu/Debian:* `sudo apt update && sudo apt install python3-pip python3-venv`
  - *macOS:* `brew install python` (includes pip and venv)
  - *Windows:* Download from [python.org](https://www.python.org/downloads/) (ensure "Add Python to PATH" is checked during setup)
- **Bash** (macOS/Linux terminal, or Git Bash / WSL on Windows)

## Quick Start

> **Important:** On a first-time run, you **cannot** use pre-cached datasets as they are not included in the repository. You must run the **Complete Pipeline** first (see below) to generate the initial data.

If you have already run the pipeline and have cached data, you can start the Streamlit dashboard immediately:
```bash
./run.sh --dashboard
```

Dependencies are pinned in `requirements.txt`. The main runner installs from that file when creating or refreshing the virtual environment.

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

* **Clean cache and generated outputs**:
  ```bash
  ./clean.sh
  ```
  *(Or use `./run.sh --clean`)*

* **Export dashboard to a standalone HTML file**:
  ```bash
  ./export.sh
  ```

* **Check all options**:
  ```bash
  ./run.sh --help
  ```

## Chapter 1.3 - Infrastructure & Storage Mapping

To re-scrape BESS and Datacentre data and regenerate the infrastructure map independently:

```bash
bash scripts/chapter_1/run_infrastructure_scrape.sh
```

Or via the main pipeline flag:

```bash
./run.sh --infrastructure
```

## Chapter 2.2 - Weather & Market Price Correlation

To re-scrape weather data and regenerate the correlation charts independently:

```bash
bash scripts/chapter_2/run_weather_scrape.sh
```

## Project Structure

- `scripts/chapter_1/`, `scripts/chapter_2/`, `scripts/chapter_3/`: primary pipeline modules grouped by dashboard chapter.
- `scripts/common/`: shared paths, constants, cache helpers, logging, and cleaning utilities.
- `dashboard/components/`: reusable Streamlit UI components.
- `dashboard/assets/`: dashboard CSS loaded by `dashboard/styles.py`.
- `tools/`: standalone maintenance/export tools.
- `docs/`: architecture, data pipeline, and deployment notes.

Top-level numbered script wrappers were removed; use the chapter modules and chapter runner scripts shown above.
