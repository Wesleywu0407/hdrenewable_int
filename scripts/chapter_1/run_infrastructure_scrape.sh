#!/usr/bin/env bash
# Run the Chapter 1.3 Infrastructure data pipeline independently.
#
# Usage:
#   bash scripts/chapter_1/run_infrastructure_scrape.sh
#
# What it does:
#   1. Activates the project virtual environment
#   2. Runs scripts.chapter_1.fetch_infrastructure_data - scrapes BESS & Datacentre data
#   3. Runs scripts.chapter_1.generate_infrastructure_charts - renders the Plotly map
#   4. Outputs to outputs/figures/fig1_4_infrastructure_map.html
#
# Prerequisites:
#   - .venv or venv must exist (run ./run.sh once to create it, or python -m venv .venv)
#   - OPENELECTRICITY_API_KEY set in .env (optional; used to enhance BESS data)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Chapter 1.3 - Infrastructure Data Refresh"
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
    echo "NOTE: OPENELECTRICITY_API_KEY not set - will use Wikipedia & curated data only."
fi

echo ""
echo "[Step 1/2] Fetching infrastructure data..."
python -m scripts.chapter_1.fetch_infrastructure_data

echo ""
echo "[Step 2/2] Generating infrastructure map..."
python -m scripts.chapter_1.generate_infrastructure_charts

echo ""
echo "Done! Map saved to: outputs/figures/fig1_4_infrastructure_map.html"
echo "Open the dashboard to view it:  ./run.sh --dashboard"
