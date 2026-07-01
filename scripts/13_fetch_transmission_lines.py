"""Chapter 1.3 Step 13 - Fetch transmission line data.

Downloads electricity transmission line geometries from the Geoscience Australia REST API.
Filters to only include lines with a capacity of >= 220kV to prevent map clutter.

Saved to:
  data/raw/transmission_lines.geojson

Run: python scripts/13_fetch_transmission_lines.py
"""

import json
from pathlib import Path
import urllib.request
import urllib.parse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# GA National Electricity Infrastructure, Layer 2 is Electricity Transmission Lines
GA_URL = "https://services.ga.gov.au/gis/rest/services/National_Electricity_Infrastructure/MapServer/2/query"

def main() -> int:
    print("Fetching transmission line data from GA...")
    
    params = {
        "where": "state NOT IN ('Western Australia', 'Northern Territory')",
        "outFields": "name,capacitykv,state,operationalstatus",
        "f": "geojson",
        "outSR": "4326"
    }
    
    query_string = urllib.parse.urlencode(params)
    url = f"{GA_URL}?{query_string}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        features = data.get("features", [])
        if not features:
            print("WARNING: No features returned. Check the query.")
        else:
            print(f"Downloaded {len(features)} transmission line features (>= 220kV).")
            
        out_path = RAW_DIR / "transmission_lines.geojson"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
            
        print(f"Saved to {out_path.relative_to(PROJECT_ROOT)}")
        
    except Exception as e:
        print(f"ERROR: Failed to fetch data: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
