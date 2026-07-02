"""Step 5 - Fetch all data needed for the Trading Market Volatility charts.

Pulls NEM Spot Market pricing and generates mock FCAS market volumes and pricing.

Run: python -m scripts.chapter_2.fetch_trading_data
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from scripts.common.api import cache_is_fresh, configure_logging
from scripts.common.constants import NEM_TZ
from scripts.common.paths import NEMOSIS_CACHE_DIR, PROJECT_ROOT, RAW_DIR

LOGGER = logging.getLogger(__name__)


def nem_now() -> datetime:
    """Current time in NEM network time, as a naive datetime (API requirement)."""
    return datetime.now(NEM_TZ).replace(tzinfo=None)


def setup_env() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("OPENELECTRICITY_API_KEY")
    if not api_key or api_key.startswith("<"):
        LOGGER.error("OPENELECTRICITY_API_KEY not set in .env.")
        sys.exit(1)


def fetch_fcas_regulation(path: Path, now: datetime) -> pd.DataFrame:
    LOGGER.info("")
    LOGGER.info("[Regulation FCAS] -> %s", path.name)
    if cache_is_fresh(path):
        df = pd.read_csv(path)
        LOGGER.info("  cache hit, skipping.")
        return df

    import nemosis
    start = "2023/12/01 00:00:00"
    end = now.strftime("%Y/%m/%d %H:%M:%S")
    cache_dir = NEMOSIS_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)

    try:
        LOGGER.info("  Fetching DISPATCHPRICE...")
        dp = nemosis.dynamic_data_compiler(start, end, "DISPATCHPRICE", str(cache_dir))
        LOGGER.info("  Fetching DISPATCHREGIONSUM...")
        ds = nemosis.dynamic_data_compiler(start, end, "DISPATCHREGIONSUM", str(cache_dir))
    except (OSError, RuntimeError, ValueError) as exc:
        LOGGER.error("  Error fetching from nemosis: %s", exc)
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
    LOGGER.info("  Saved Regulation FCAS: %s rows", len(df))
    return df


def fetch_fcas_contingency(path: Path, now: datetime) -> pd.DataFrame:
    LOGGER.info("")
    LOGGER.info("[Contingency FCAS] -> %s", path.name)
    if cache_is_fresh(path):
        df = pd.read_csv(path)
        LOGGER.info("  cache hit, skipping.")
        return df

    import nemosis
    start = "2023/12/01 00:00:00"
    end = now.strftime("%Y/%m/%d %H:%M:%S")
    cache_dir = NEMOSIS_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)

    try:
        LOGGER.info("  Fetching DISPATCHPRICE...")
        dp = nemosis.dynamic_data_compiler(start, end, "DISPATCHPRICE", str(cache_dir))
        LOGGER.info("  Fetching DISPATCHREGIONSUM...")
        ds = nemosis.dynamic_data_compiler(start, end, "DISPATCHREGIONSUM", str(cache_dir))
    except (OSError, RuntimeError, ValueError) as exc:
        LOGGER.error("  Error fetching from nemosis: %s", exc)
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
        # 12.0 converts 5-minute dispatch intervals to hourly revenue.
        merged[srv] = merged[p_col] * merged[v_col] / 12.0

    daily_value = merged.groupby(merged["SETTLEMENTDATE"].dt.date)[list(services.keys())].sum().reset_index()
    for srv in services.keys():
        daily_value[srv] = daily_value[srv] / 1e6

    daily_value = daily_value.rename(columns={"SETTLEMENTDATE": "interval"})

    daily_value.to_csv(path, index=False)
    LOGGER.info("  Saved Contingency FCAS: %s rows", len(daily_value))
    return daily_value


def main() -> int:
    configure_logging()
    setup_env()
    now = nem_now()

    fetch_fcas_regulation(RAW_DIR / "fcas_regulation.csv", now)
    fetch_fcas_contingency(RAW_DIR / "fcas_contingency.csv", now)

    LOGGER.info("")
    LOGGER.info("Done fetching trading data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
