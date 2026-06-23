"""Step 5 — Fetch all data needed for the Trading Market Volatility charts.

Pulls NEM Spot Market pricing and generates mock FCAS market volumes and pricing.

Run: python scripts/05_fetch_trading_data.py
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import random

import numpy as np
import pandas as pd
from dotenv import load_dotenv

NEM_TZ = timezone(timedelta(hours=10))

def nem_now() -> datetime:
    """Current time in NEM network time, as a naive datetime (API requirement)."""
    return datetime.now(NEM_TZ).replace(tzinfo=None)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(PROJECT_ROOT / ".env")
API_KEY = os.getenv("OPENELECTRICITY_API_KEY")
if not API_KEY or API_KEY.startswith("<"):
    print("ERROR: OPENELECTRICITY_API_KEY not set in .env.")
    sys.exit(1)

from openelectricity import OEClient  # noqa: E402
from openelectricity.types import MarketMetric  # noqa: E402

CACHE_MAX_AGE_H = 24

def cache_is_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age_h = (time.time() - path.stat().st_mtime) / 3600
    return age_h < CACHE_MAX_AGE_H

def summarize(path: Path, df: pd.DataFrame) -> None:
    size_kb = path.stat().st_size / 1024
    date_cols = [c for c in df.columns if "interval" in c.lower() or "date" in c.lower()]
    drange = ""
    if date_cols:
        col = date_cols[0]
        drange = f" | {col}: {df[col].min()} -> {df[col].max()}"
    print(f"  saved {path.name}: {len(df):,} rows, {size_kb:.1f} KB{drange}")

def timeseries_to_df(response) -> pd.DataFrame:
    records: list[dict] = []
    for ts in response.data:
        metric = getattr(ts, "metric", getattr(ts, "name", None))
        unit = getattr(ts, "unit", None)
        for series in ts.results:
            cols = series.columns
            labels = cols.model_dump() if hasattr(cols, "model_dump") else dict(cols or {})
            labels = {k: v for k, v in labels.items() if v is not None}
            series_name = getattr(series, "name", None)
            
            # Extract network_region if available in series.name
            if "network_region" not in labels and series_name:
                head = series_name.split("|", 1)[0]
                parts = head.split("_")
                for token in ["NSW1", "QLD1", "VIC1", "SA1", "TAS1"]:
                    if token in parts:
                        labels["network_region"] = token
                        break

            for point in series.data:
                ts_val, val = point.root if hasattr(point, "root") else point
                rec = {
                    "interval": ts_val,
                    "value": val,
                    "metric": str(metric),
                    "unit": unit,
                    "series_name": series_name,
                    **labels,
                }
                records.append(rec)
    df = pd.DataFrame(records)
    if not df.empty:
        df["interval"] = pd.to_datetime(df["interval"])
    return df

def fetch_cached(path: Path, label: str, fetch_fn) -> pd.DataFrame | None:
    print(f"\n[{label}] -> {path.name}")
    if cache_is_fresh(path):
        df = pd.read_csv(path, low_memory=False)
        if "interval" in df.columns:
            df["interval"] = pd.to_datetime(df["interval"])
        print(f"  cache hit (< {CACHE_MAX_AGE_H}h old), skipping API call.")
        summarize(path, df)
        return df
    try:
        df = fetch_fn()
    except Exception as exc:
        print(f"  FETCH FAILED: {type(exc).__name__}: {exc}")
        if path.exists():
            print("  using stale cache as fallback.")
            df_fallback = pd.read_csv(path, low_memory=False)
            if "interval" in df_fallback.columns:
                df_fallback["interval"] = pd.to_datetime(df_fallback["interval"])
            return df_fallback
        return None
    if df is None or df.empty:
        print("  WARNING: API returned no data.")
        return df

    if path.exists():
        print("  merging new data with existing historical data...")
        df_old = pd.read_csv(path, low_memory=False)
        if "interval" in df_old.columns:
            df_old["interval"] = pd.to_datetime(df_old["interval"])
        if "interval" in df.columns:
            df["interval"] = pd.to_datetime(df["interval"])
        
        combined = pd.concat([df_old, df], ignore_index=True)
        if "interval" in combined.columns:
            subset_cols = [c for c in combined.columns if c not in ["value", "price"]]
            combined = combined.drop_duplicates(subset=subset_cols, keep="last")
            combined = combined.sort_values("interval")
        else:
            combined = combined.drop_duplicates(keep="last")
        df = combined.copy()

    df.to_csv(path, index=False)
    summarize(path, df)
    return df

def generate_mock_fcas_regulation(path: Path, now: datetime) -> pd.DataFrame:
    print(f"\n[Regulation FCAS (Mock)] -> {path.name}")
    dates = [now - timedelta(days=i) for i in range(30, 0, -1)]
    records = []
    
    raise_price_base = 15.0
    lower_price_base = 10.0
    raise_vol_base = 250.0
    lower_vol_base = 200.0
    
    for dt in dates:
        r_price = max(0, raise_price_base + np.random.normal(0, 5))
        l_price = max(0, lower_price_base + np.random.normal(0, 3))
        r_vol = max(50, raise_vol_base + np.random.normal(0, 30))
        l_vol = max(50, lower_vol_base + np.random.normal(0, 20))
        
        if random.random() > 0.9:
            r_price += random.uniform(20, 80)
            
        records.append({
            "interval": dt.strftime("%Y-%m-%d"),
            "raise_price": r_price,
            "lower_price": l_price,
            "raise_volume": r_vol,
            "lower_volume": l_vol
        })
        
    df = pd.DataFrame(records)
    df.to_csv(path, index=False)
    print(f"  Generated mock Regulation FCAS: {len(df)} rows")
    return df

def generate_mock_fcas_contingency(path: Path, now: datetime) -> pd.DataFrame:
    print(f"\n[Contingency FCAS (Mock)] -> {path.name}")
    dates = []
    current_date = now.replace(day=1)
    for _ in range(12):
        dates.append(current_date)
        month = current_date.month - 1
        year = current_date.year
        if month == 0:
            month = 12
            year -= 1
        current_date = current_date.replace(year=year, month=month)
    dates.reverse()
    
    records = []
    for dt in dates:
        fast_raise = random.uniform(5, 15)
        fast_lower = random.uniform(2, 8)
        slow_raise = random.uniform(8, 20)
        slow_lower = random.uniform(3, 10)
        delayed_raise = random.uniform(10, 25)
        delayed_lower = random.uniform(5, 12)
        
        if dt.month in [1, 2, 6, 7]:
            fast_raise *= 1.5
            slow_raise *= 1.3
            
        records.append({
            "interval": dt.strftime("%Y-%m"),
            "fast_raise": fast_raise,
            "fast_lower": fast_lower,
            "slow_raise": slow_raise,
            "slow_lower": slow_lower,
            "delayed_raise": delayed_raise,
            "delayed_lower": delayed_lower
        })
        
    df = pd.DataFrame(records)
    df.to_csv(path, index=False)
    print(f"  Generated mock Contingency FCAS: {len(df)} rows")
    return df

def main() -> int:
    now = nem_now()

    generate_mock_fcas_regulation(RAW_DIR / "fcas_regulation_mock.csv", now)
    generate_mock_fcas_contingency(RAW_DIR / "fcas_contingency_mock.csv", now)

    print("\nDone fetching trading data.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
