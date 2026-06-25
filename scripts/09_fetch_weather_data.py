"""Chapter 2.4 - Fetch Weather Data & Merge with Market Data.

This script fetches historical weather data from Open-Meteo for Brisbane (QLD)
and merges it with historical spot prices and demand data from OpenElectricity.

Output:
  - data/raw/weather_price_correlation.csv
"""

from __future__ import annotations

import os
import sys
import requests
from datetime import timedelta, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from openelectricity import OEClient
from openelectricity.types import MarketMetric

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILE = RAW_DIR / "weather_price_correlation.csv"
SPOT_PRICE_FILE = RAW_DIR / "qld_spot_prices.csv"

NEM_TZ = timezone(timedelta(hours=10))

# Brisbane coordinates
LATITUDE = -27.4705
LONGITUDE = 153.0260

def fetch_weather_data(start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch hourly historical weather from Open-Meteo."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,direct_radiation,wind_speed_10m",
        "timezone": "Australia/Brisbane",
    }
    print(f"Fetching weather data from Open-Meteo ({start_date} to {end_date})...")
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    
    data = resp.json()["hourly"]
    df = pd.DataFrame(data)
    # The 'time' column is already in the specified timezone but as string, e.g. "2025-06-23T00:00"
    df["interval"] = pd.to_datetime(df["time"]).dt.tz_localize(None)
    df = df.drop(columns=["time"])
    return df

def fetch_demand_data(client: OEClient, region: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Fetch hourly demand data from OEClient."""
    rows = []
    window = timedelta(days=31)
    cur = start
    end_tz = end
    
    print(f"Fetching {region} demand data from OpenElectricity...")
    while cur < end_tz:
        chunk_end = min(cur + window, end_tz)
        try:
            resp = client.get_market(
                network_code="NEM",
                metrics=[MarketMetric.DEMAND],
                interval="1h",
                date_start=cur,
                date_end=chunk_end,
                network_region=region,
            )
            for ts in resp.data:
                for series in ts.results:
                    for point in series.data:
                        t, v = point.root if hasattr(point, "root") else point
                        rows.append({"interval": t, "demand": v})
        except Exception as exc:
            print(f"    demand chunk {cur:%Y-%m-%d} failed: {exc}")
        cur = chunk_end
        
    df = pd.DataFrame(rows)
    if not df.empty:
        df["interval"] = pd.to_datetime(df["interval"], utc=True).dt.tz_convert(NEM_TZ).dt.tz_localize(None)
        df = df.drop_duplicates(subset=["interval"]).sort_values("interval")
    return df

def main():
    load_dotenv(PROJECT_ROOT / ".env")
    if not os.getenv("OPENELECTRICITY_API_KEY"):
        print("ERROR: OPENELECTRICITY_API_KEY not set in .env.")
        sys.exit(1)
        
    if not SPOT_PRICE_FILE.exists():
        print(f"ERROR: {SPOT_PRICE_FILE} not found. Please run earlier scripts first.")
        sys.exit(1)
        
    # 1. Load Price Data
    print(f"Loading {SPOT_PRICE_FILE}...")
    df_price = pd.read_csv(SPOT_PRICE_FILE, low_memory=False)
    df_price["interval"] = pd.to_datetime(df_price["interval"]).dt.tz_localize(None)
    
    min_time = df_price["interval"].min()
    max_time = df_price["interval"].max()
    
    start_date_str = min_time.strftime("%Y-%m-%d")
    end_date_str = max_time.strftime("%Y-%m-%d")
    
    # 2. Fetch Weather Data
    df_weather = fetch_weather_data(start_date_str, end_date_str)
    
    # 3. Fetch Demand Data
    with OEClient() as client:
        df_demand = fetch_demand_data(client, "QLD1", min_time, max_time)
        
    # 4. Merge all data on interval
    print("Merging data...")
    df_merged = df_price.merge(df_weather, on="interval", how="inner")
    if not df_demand.empty:
        df_merged = df_merged.merge(df_demand, on="interval", how="inner")
    else:
        print("WARNING: No demand data fetched, output will not have demand.")
        
    # 5. Save output
    df_merged.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved merged dataset to {OUTPUT_FILE} ({len(df_merged)} rows)")
    
if __name__ == "__main__":
    main()
