#!/usr/bin/env bash
# Run the Chapter 1.1 QLD Renewables data pipeline independently.
#
# Usage:
#   bash scripts/run_qld_scrape.sh
#
# What it does:
#   1. Activates the project virtual environment
#   2. Runs 01_fetch_nem_data.py — refreshes shared NEM datasets
#   3. Runs 03_fetch_qld_data.py — refreshes QLD renewables datasets
#   4. Runs 04_generate_qld_charts.py — renders QLD renewables charts
#
# Prerequisites:
#   - .venv or venv must exist (run ./run.sh once to create it, or python -m venv .venv)
#   - OPENELECTRICITY_API_KEY set in .env if fresh OpenElectricity data is required

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Chapter 1.1 — QLD Renewables Data Refresh"
echo "=========================================="
echo "Project root: $PROJECT_ROOT"
echo ""

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "ERROR: No virtual environment found. Run './run.sh' once first to set it up."
    exit 1
fi

# Load API key if available
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs) 2>/dev/null || true
fi

if [ -z "$OPENELECTRICITY_API_KEY" ]; then
    echo "WARNING: OPENELECTRICITY_API_KEY is not set. Data fetch might fail or use cached data."
fi

echo ""
echo "[Step 1/3] Fetching shared NEM data..."
python scripts/01_fetch_nem_data.py

echo ""
echo "[Step 2/3] Fetching QLD renewables data..."
python scripts/03_fetch_qld_data.py

echo ""
echo "[Step 3/3] Generating QLD renewables charts..."
python scripts/04_generate_qld_charts.py

echo ""
echo "Done! QLD charts saved to: outputs/figures/"
echo "Open the dashboard to view them:  ./run.sh --dashboard"
