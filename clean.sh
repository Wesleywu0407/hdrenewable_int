#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Cleaning cache directories..."
echo "=========================================="

if [ -d "nemosis_cache" ]; then
    rm -rf nemosis_cache/
    echo "  Deleted nemosis_cache/"
fi

if [ -d "data/raw" ]; then
    find data/raw -type f ! -name 'master_*.csv' -delete
    echo "  Deleted non-master files in data/raw/"
fi

if [ -d "outputs" ]; then
    rm -rf outputs/
    echo "  Deleted outputs/ directory"
fi

if [ -f "dashboard_exported.html" ]; then
    rm dashboard_exported.html
    echo "  Deleted dashboard_exported.html"
fi

echo "Cache and generated outputs cleaned."
