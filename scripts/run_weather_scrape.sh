#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Ensure virtual environment exists
if [ ! -d ".venv" ]; then
    echo "ERROR: Virtual environment not found. Please run ./run.sh first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if API key is set when fetching
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs) 2>/dev/null || true
fi

echo "=========================================="
echo "1. Fetching Weather & Market Correlation Data..."
echo "=========================================="
python scripts/09_fetch_weather_data.py

echo "=========================================="
echo "2. Generating Weather & Market Charts..."
echo "=========================================="
python scripts/10_generate_weather_charts.py

echo "=========================================="
echo "Weather scrape completed successfully!"
echo "=========================================="
