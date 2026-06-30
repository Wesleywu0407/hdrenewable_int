#!/bin/bash

if [ -z "$OPENELECTRICITY_API_KEY" ]; then
  echo "Warning: OPENELECTRICITY_API_KEY is not set. The scrape might fail if it requires authentication."
fi

python scripts/01_fetch_nem_data.py
python scripts/02_generate_charts.py
