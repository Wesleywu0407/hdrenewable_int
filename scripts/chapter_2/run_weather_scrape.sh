#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
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
python -m scripts.chapter_2.fetch_weather_data

echo "=========================================="
echo "2. Generating Weather & Market Charts..."
echo "=========================================="
python -m scripts.chapter_2.generate_weather_charts

echo "=========================================="
echo "Weather scrape completed successfully!"
echo "=========================================="
