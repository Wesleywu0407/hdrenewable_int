#!/bin/bash

if [ -z "$OPENELECTRICITY_API_KEY" ]; then
  echo "Warning: OPENELECTRICITY_API_KEY is not set. The scrape might fail if it requires authentication."
fi

python -m scripts.chapter_1.fetch_nem_data
python -m scripts.chapter_1.generate_nem_charts
