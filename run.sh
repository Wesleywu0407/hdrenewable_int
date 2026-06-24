#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Define default actions
FETCH=false
GENERATE=false
DASHBOARD=false
ALL=true

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --fetch) FETCH=true; ALL=false ;;
        --generate) GENERATE=true; ALL=false ;;
        --dashboard) DASHBOARD=true; ALL=false ;;
        --help|-h)
            echo "Usage: ./run.sh [options]"
            echo "Options:"
            echo "  --fetch       Fetch raw datasets from OpenElectricity API"
            echo "  --generate    Generate interactive HTML & PNG charts"
            echo "  --dashboard   Start the Streamlit dashboard"
            echo "  -h, --help    Show this help message"
            echo ""
            echo "If no options are provided, the script runs the complete pipeline (fetch -> generate -> dashboard)."
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# If no flags are set, run everything
if [ "$ALL" = true ]; then
    FETCH=true
    GENERATE=true
    DASHBOARD=true
fi

# Ensure virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    if command -v virtualenv &> /dev/null; then
        virtualenv .venv
    else
        python3 -m venv .venv
    fi
fi

# Activate virtual environment
source .venv/bin/activate

# Ensure requirements are installed
echo "Checking and verifying dependencies..."
pip install openelectricity[analysis] pandas plotly python-dotenv jupyter pyarrow kaleido "streamlit>=1.32" nemosis --quiet

# Execute Fetch phase
if [ "$FETCH" = true ]; then
    echo "=========================================="
    echo "1. Fetching raw NEM and QLD data..."
    echo "=========================================="
    # Check if API key is set when fetching
    if [ -f ".env" ]; then
        # Use export so scripts see it
        export $(grep -v '^#' .env | xargs) 2>/dev/null || true
    fi
    if [ -z "$OPENELECTRICITY_API_KEY" ]; then
        echo "WARNING: OPENELECTRICITY_API_KEY is not set. Data fetch might fail or use cached data."
    fi
    python scripts/01_fetch_nem_data.py
    python scripts/03_fetch_qld_data.py
    python scripts/05_fetch_trading_data.py
fi

# Execute Generate phase
if [ "$GENERATE" = true ]; then
    echo "=========================================="
    echo "2. Generating charts..."
    echo "=========================================="
    python scripts/02_generate_charts.py
    python scripts/04_generate_qld_charts.py
    python scripts/06_generate_trading_charts.py

fi

# Execute Dashboard phase
if [ "$DASHBOARD" = true ]; then
    echo "=========================================="
    echo "3. Starting Streamlit dashboard..."
    echo "=========================================="
    streamlit run dashboard/app.py
fi
