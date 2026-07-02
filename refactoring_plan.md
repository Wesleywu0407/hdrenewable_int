# Codebase Refactoring & Production-Readiness Plan

> **Guiding Principle: Zero Functional Changes**
> *All refactoring steps proposed below are strictly structural and organizational. We will **not change any existing functionality, data outputs, or underlying logic** at all. The goal is purely to restructure the code to make it more readable, modular, testable, and production-ready while ensuring the dashboard and scripts behave exactly as they do today.*

Based on a thorough analysis of the existing codebase, I propose the following refactoring steps to enhance readability, modularity, and production readiness.

## 1. Project Structure & Modularity (Grouping by Chapter)
Currently, a lot of logic is mixed within large script files, and scripts are dumped into a single flat `scripts/` directory. We should introduce a domain-driven structure grouped by "Chapters", which aligns with how the dashboard and report are presented.

- **Group by Chapter:** Instead of a flat list (`01_fetch...`, `02_generate...`, `10_generate...`), group the scripts, data outputs, and documentation into subdirectories for each chapter (e.g., `scripts/chapter_1/`, `scripts/chapter_2/`). This will make it much easier to find the relevant code for a specific section of the dashboard.
- **Create a `config.py` or `constants.py`:** Move hardcoded mappings (`FUELTECH_POWER_COLS`, `NEM_REGIONS`) from individual scripts into a centralized config.
- **Create a `utils/api.py` (or similar):** Extract reusable functions like `cache_is_fresh`, `fetch_cached`, and `summarize` into a common utility module so they can be reused across all `0X_fetch_...` scripts.
- **Data Cleaning Separation:** In `dashboard/app.py`, functions like `load_infrastructure_data` perform data cleaning. This logic belongs in the data pipeline (`scripts/`) before the dashboard consumes it. 
- **Relocate Export Scripts:** Move standalone scripts like `export_stlite.py` out of the root directory and into a dedicated `tools/` or `scripts/export/` directory to keep the root directory clean.

## 2. Refactoring `dashboard/app.py`
The main `app.py` file is currently over 1,300 lines long, making it difficult to maintain.
- **Component Extraction:** Move UI components into a dedicated `dashboard/components/` directory (e.g., `components/sidebar.py`, `components/refresh_ui.py`).
- **CSS Separation:** Move large blocks of inline CSS into the existing `styles.py` or a dedicated `.css` file.
- **Logic Extraction:** Log parsing logic should be moved to a `dashboard/utils.py`.

## 3. Refactoring `scripts/01_fetch_nem_data.py`
- **Standardize Imports & Initialization:** All imports should be at the top of the file, following PEP 8. Environment checks should be moved inside a function (e.g., `setup_env()`).
- **Break Down `main()`:** The `main()` function fetches multiple distinct datasets in a single massive block. It should be refactored to call smaller, descriptive functions (e.g., `fetch_master_nem()`).
- **Error Handling:** Replace broad catch-all exceptions (`except Exception as exc:`) with specific API or Network exceptions.

## 4. Robust Dependency Management (Crucial for Production)
- **Lock Dependencies:** Currently, `run.sh` installs packages via a loose `pip install ...` command. For production, we must freeze dependencies using a `requirements.txt` or a modern tool like `poetry`/`uv` (`pyproject.toml`). This prevents the dashboard from breaking if a package (like `pandas` or `streamlit`) releases an incompatible update.

## 5. Testing & Quality Assurance
- **Unit & Integration Tests:** Introduce a `tests/` directory using `pytest`. We should write tests to mock the API responses and verify our data transformations, ensuring the pipeline doesn't break when data structures change.
- **Linting & Formatting:** Enforce consistent code style using tools like `ruff` or `black`, and static type checking using `mypy`.

## 6. Comprehensive Documentation (`docs/`)
- **Extracting "What This Does":** We removed the verbose descriptions from the `README.md` to make it concise. We should create a dedicated `docs/` folder containing:
  - `docs/architecture.md`: How the dashboard and scraping scripts interact.
  - `docs/data_pipeline.md`: The "What this does" explanations for each script, where data comes from, and what transformations occur.
  - `docs/deployment.md`: Instructions on how to deploy this to a production server (e.g., Docker, AWS EC2, Streamlit Cloud).

## 7. Logging & Monitoring
- **Replace `print()` with `logging`:** Use Python's built-in `logging` module for tracking pipeline progress (with timestamps and log levels like INFO, DEBUG, ERROR).
- **Alerting:** If this pipeline runs on a schedule (e.g., via cron), failures should trigger an alert (like an email or a Slack webhook) so you don't find out the data is stale days later.

## 8. Cleanup
- **Delete this plan:** Once all the refactoring steps outlined in this document are completed, this `refactoring_plan.md` file should be deleted.
