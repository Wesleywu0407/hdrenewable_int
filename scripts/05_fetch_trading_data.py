"""Step 5 - Fetch all data needed for the Trading Market Volatility charts.

Pulls NEM Spot Market pricing and generates mock FCAS market volumes and pricing.

Run: python scripts/05_fetch_trading_data.py
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

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

from openelectricity import OEClient  # noqa: E402 (imported for potential future use)

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

def fetch_fcas_regulation(path: Path, now: datetime) -> pd.DataFrame:
    print(f"\n[Regulation FCAS] -> {path.name}")
    if cache_is_fresh(path):
        df = pd.read_csv(path)
        print("  cache hit, skipping.")
        return df

    import nemosis
    start = "2023/12/01 00:00:00"
    end = now.strftime("%Y/%m/%d %H:%M:%S")
    cache_dir = PROJECT_ROOT / "nemosis_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        print("  Fetching DISPATCHPRICE...")
        dp = nemosis.dynamic_data_compiler(start, end, "DISPATCHPRICE", str(cache_dir))
        print("  Fetching DISPATCHREGIONSUM...")
        ds = nemosis.dynamic_data_compiler(start, end, "DISPATCHREGIONSUM", str(cache_dir))
    except Exception as e:
        print(f"  Error fetching from nemosis: {e}")
        return pd.DataFrame()

    dp["SETTLEMENTDATE"] = pd.to_datetime(dp["SETTLEMENTDATE"])
    ds["SETTLEMENTDATE"] = pd.to_datetime(ds["SETTLEMENTDATE"])
    
    # Convert columns to float
    for col in ["RAISEREGRRP", "LOWERREGRRP"]:
        dp[col] = pd.to_numeric(dp[col], errors="coerce")
    for col in ["RAISEREGLOCALDISPATCH", "LOWERREGLOCALDISPATCH"]:
        ds[col] = pd.to_numeric(ds[col], errors="coerce")
    
    dp_daily = dp.groupby(dp["SETTLEMENTDATE"].dt.date).agg({
        "RAISEREGRRP": "mean",
        "LOWERREGRRP": "mean"
    }).reset_index()
    
    ds_daily = ds.groupby(ds["SETTLEMENTDATE"].dt.date).agg({
        "RAISEREGLOCALDISPATCH": "mean",
        "LOWERREGLOCALDISPATCH": "mean"
    }).reset_index()

    df = pd.merge(dp_daily, ds_daily, on="SETTLEMENTDATE")
    df = df.rename(columns={
        "SETTLEMENTDATE": "interval",
        "RAISEREGRRP": "raise_price",
        "LOWERREGRRP": "lower_price",
        "RAISEREGLOCALDISPATCH": "raise_volume",
        "LOWERREGLOCALDISPATCH": "lower_volume"
    })
    
    df.to_csv(path, index=False)
    print(f"  Saved Regulation FCAS: {len(df)} rows")
    return df

def fetch_fcas_contingency(path: Path, now: datetime) -> pd.DataFrame:
    print(f"\n[Contingency FCAS] -> {path.name}")
    if cache_is_fresh(path):
        df = pd.read_csv(path)
        print("  cache hit, skipping.")
        return df

    import nemosis
    start = "2023/12/01 00:00:00"
    end = now.strftime("%Y/%m/%d %H:%M:%S")
    cache_dir = PROJECT_ROOT / "nemosis_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        print("  Fetching DISPATCHPRICE...")
        dp = nemosis.dynamic_data_compiler(start, end, "DISPATCHPRICE", str(cache_dir))
        print("  Fetching DISPATCHREGIONSUM...")
        ds = nemosis.dynamic_data_compiler(start, end, "DISPATCHREGIONSUM", str(cache_dir))
    except Exception as e:
        print(f"  Error fetching from nemosis: {e}")
        return pd.DataFrame()

    dp["SETTLEMENTDATE"] = pd.to_datetime(dp["SETTLEMENTDATE"])
    ds["SETTLEMENTDATE"] = pd.to_datetime(ds["SETTLEMENTDATE"])
    
    merged = pd.merge(dp, ds, on=["SETTLEMENTDATE", "REGIONID"])
    
    services = {
        "fast_raise": ("RAISE6SECRRP", "RAISE6SECLOCALDISPATCH"),
        "fast_lower": ("LOWER6SECRRP", "LOWER6SECLOCALDISPATCH"),
        "slow_raise": ("RAISE60SECRRP", "RAISE60SECLOCALDISPATCH"),
        "slow_lower": ("LOWER60SECRRP", "LOWER60SECLOCALDISPATCH"),
        "delayed_raise": ("RAISE5MINRRP", "RAISE5MINLOCALDISPATCH"),
        "delayed_lower": ("LOWER5MINRRP", "LOWER5MINLOCALDISPATCH")
    }
    
    for srv, (p_col, v_col) in services.items():
        merged[p_col] = pd.to_numeric(merged[p_col], errors="coerce")
        merged[v_col] = pd.to_numeric(merged[v_col], errors="coerce")
        # 12.0 converts 5-minute dispatch intervals to hourly revenue (12 × 5min = 1hr)
        merged[srv] = merged[p_col] * merged[v_col] / 12.0
        
    daily_value = merged.groupby(merged["SETTLEMENTDATE"].dt.date)[list(services.keys())].sum().reset_index()
    for srv in services.keys():
        daily_value[srv] = daily_value[srv] / 1e6
        
    daily_value = daily_value.rename(columns={"SETTLEMENTDATE": "interval"})
    
    daily_value.to_csv(path, index=False)
    print(f"  Saved Contingency FCAS: {len(daily_value)} rows")
    return daily_value

def main() -> int:
    now = nem_now()

    fetch_fcas_regulation(RAW_DIR / "fcas_regulation.csv", now)
    fetch_fcas_contingency(RAW_DIR / "fcas_contingency.csv", now)

    print("\nDone fetching trading data.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
