#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Checking script2stlite installation..."
pip install script2stlite --quiet

echo "Running export script..."
python export_stlite.py

echo "========================================="
echo "Success! The dashboard has been exported to: dashboard_exported.html"
echo "You can now open this file in any web browser."
