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
