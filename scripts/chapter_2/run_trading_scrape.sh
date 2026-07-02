#!/usr/bin/env bash
# Run the Chapter 2.1 Trading Market data pipeline independently.
#
# Usage:
#   bash scripts/chapter_2/run_trading_scrape.sh
#
# What it does:
#   1. Activates the project virtual environment
#   2. Runs scripts.chapter_1.fetch_qld_data - refreshes QLD spot price data
#   3. Runs scripts.chapter_2.fetch_trading_data - refreshes FCAS market datasets
#   4. Runs scripts.chapter_2.generate_trading_charts - renders trading market charts
#
# Prerequisites:
#   - .venv or venv must exist (run ./run.sh once to create it, or python -m venv .venv)
#   - OPENELECTRICITY_API_KEY set in .env if fresh OpenElectricity data is required

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Chapter 2.1 - Trading Market Data Refresh"
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
echo "[Step 1/3] Fetching QLD spot price data..."
python -m scripts.chapter_1.fetch_qld_data

echo ""
echo "[Step 2/3] Fetching trading market data..."
python -m scripts.chapter_2.fetch_trading_data

echo ""
echo "[Step 3/3] Generating trading market charts..."
python -m scripts.chapter_2.generate_trading_charts

echo ""
echo "Done! Trading charts saved to: outputs/figures/"
echo "Open the dashboard to view them:  ./run.sh --dashboard"
