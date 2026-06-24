"""Step 3 — Fetch all NEM data needed for the 5 charts.

Pulls 5 datasets from the OpenElectricity API and caches each as Parquet under
data/raw/. If a cache file exists and is < 24h old, the API call is skipped.

Run: python scripts/01_fetch_nem_data.py
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# NEM operates on fixed Australian Eastern Standard Time (UTC+10, no DST).
# The API requires timezone-NAIVE datetimes expressed in this network time.
NEM_TZ = timezone(timedelta(hours=10))


def nem_now() -> datetime:
    """Current time in NEM network time, as a naive datetime (API requirement)."""
    return datetime.now(NEM_TZ).replace(tzinfo=None)

import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(PROJECT_ROOT / ".env")
API_KEY = os.getenv("OPENELECTRICITY_API_KEY")
if not API_KEY or API_KEY.startswith("<"):
    print("ERROR: OPENELECTRICITY_API_KEY not set in .env.")
    sys.exit(1)

from openelectricity import OEClient  # noqa: E402
from openelectricity.types import DataMetric, FueltechGroupType, UnitStatusType, MarketMetric  # noqa: E402

CACHE_MAX_AGE_H = 24
NEM_REGIONS = ["NSW1", "QLD1", "VIC1", "SA1", "TAS1"]

# --------------------------------------------------------------------------- #
# Fueltech ID → Wide-format column name mappings (must match master CSV headers)
# NOTE: The double space in " -  MW" is intentional and matches the team files.
# --------------------------------------------------------------------------- #
FUELTECH_POWER_COLS: dict[str, str] = {
    "battery_charging": "Battery (Charging) -  MW",
    "pumps": "Pumps -  MW",
    "coal_brown": "Coal (Brown) -  MW",
    "coal_black": "Coal (Black) -  MW",
    "bioenergy_biomass": "Bioenergy (Biomass) -  MW",
    "bioenergy_biogas": "Bioenergy (Biogas) -  MW",
    "distillate": "Distillate -  MW",
    "gas_steam": "Gas (Steam) -  MW",
    "gas_ccgt": "Gas (CCGT) -  MW",
    "gas_ocgt": "Gas (OCGT) -  MW",
    "gas_recip": "Gas (Reciprocating) -  MW",
    "gas_wcmg": "Gas (Waste Coal Mine) -  MW",
    "battery_discharging": "Battery (Discharging) -  MW",
    "hydro": "Hydro -  MW",
    "wind": "Wind -  MW",
    "solar_utility": "Solar (Utility) -  MW",
    "solar_rooftop": "Solar (Rooftop) -  MW",
}

FUELTECH_EMISSIONS_COLS: dict[str, str] = {
    "coal_brown": "Coal (Brown) Emissions Vol - tCO\u2082e",
    "coal_black": "Coal (Black) Emissions Vol - tCO\u2082e",
    "bioenergy_biomass": "Bioenergy (Biomass) Emissions Vol - tCO\u2082e",
    "bioenergy_biogas": "Bioenergy (Biogas) Emissions Vol - tCO\u2082e",
    "distillate": "Distillate Emissions Vol - tCO\u2082e",
    "gas_steam": "Gas (Steam) Emissions Vol - tCO\u2082e",
    "gas_ccgt": "Gas (CCGT) Emissions Vol - tCO\u2082e",
    "gas_ocgt": "Gas (OCGT) Emissions Vol - tCO\u2082e",
    "gas_recip": "Gas (Reciprocating) Emissions Vol - tCO\u2082e",
    "gas_wcmg": "Gas (Waste Coal Mine) Emissions Vol - tCO\u2082e",
}

# COMMUNITY plan only exposes ~the last 730 days of history, and the 1M interval
# is capped at a 732-day range per request. We clamp long-range queries to this
# window. NOTE: this means 2020-2023 data is NOT available on this plan — the
# 5-year deliverables (Fig 2, Fig 4) are limited to the last ~2 years.
MAX_HISTORY_DAYS = 728


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def cache_is_fresh(path: Path, max_age_h: float = CACHE_MAX_AGE_H) -> bool:
    """True if the file exists and is younger than max_age_h hours."""
    if not path.exists():
        return False
    age_h = (time.time() - path.stat().st_mtime) / 3600
    return age_h < max_age_h


def summarize(path: Path, df: pd.DataFrame) -> None:
    """Print a short summary of a saved dataset."""
    size_kb = path.stat().st_size / 1024
    date_cols = [c for c in df.columns if "interval" in c.lower() or "date" in c.lower()]
    drange = ""
    if date_cols:
        col = date_cols[0]
        drange = f" | {col}: {df[col].min()} -> {df[col].max()}"
    print(f"  saved {path.name}: {len(df):,} rows, {size_kb:.1f} KB{drange}")


def _region_from_name(name: str | None) -> str | None:
    """Extract a NEM region code (e.g. 'NSW1') from a series name.

    Series names look like 'energy_NSW1|coal' (region + group) or 'energy_coal'
    (no region). Region tokens are the known NEM region codes.
    """
    if not name:
        return None
    # Token before the first '|' after stripping the leading 'metric_' prefix.
    head = name.split("|", 1)[0]
    parts = head.split("_")
    for token in parts:
        if token in NEM_REGIONS:
            return token
    return None


def timeseries_to_df(response) -> pd.DataFrame:
    """Flatten an OpenElectricity TimeSeriesResponse into a tidy long DataFrame.

    Columns: interval, value, metric, unit, <grouping columns...>
    """
    records: list[dict] = []
    for ts in response.data:  # one TimeSeries per metric
        metric = getattr(ts, "metric", getattr(ts, "name", None))
        unit = getattr(ts, "unit", None)
        for series in ts.results:
            # series.columns is a pydantic model carrying grouping labels
            # (unit_code, fueltech, fueltech_group, renewable, network_region).
            cols = series.columns
            labels = cols.model_dump() if hasattr(cols, "model_dump") else dict(cols or {})
            # Drop label keys that are entirely None for this series.
            labels = {k: v for k, v in labels.items() if v is not None}
            series_name = getattr(series, "name", None)
            # The network_region is encoded in series.name (e.g. "energy_NSW1|coal")
            # rather than in the columns model — recover it when missing.
            if "network_region" not in labels:
                region = _region_from_name(series_name)
                if region:
                    labels["network_region"] = region
            for point in series.data:
                # Each point is a RootModel wrapping a (timestamp, value) tuple.
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
    """Generic cache-or-fetch wrapper with graceful error handling."""
    print(f"\n[{label}] -> {path.name}")
    if cache_is_fresh(path):
        df = pd.read_csv(path, low_memory=False)
        for col in ["interval", "commissioning_date", "closure_date", "commenced", "retired"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        print(f"  cache hit (< {CACHE_MAX_AGE_H}h old), skipping API call.")
        summarize(path, df)
        return df
    try:
        df = fetch_fn()
    except Exception as exc:  # noqa: BLE001
        print(f"  FETCH FAILED: {type(exc).__name__}: {exc}")
        if path.exists():
            print("  using stale cache as fallback.")
            df_fallback = pd.read_csv(path, low_memory=False)
            for col in ["interval", "commissioning_date", "closure_date", "commenced", "retired"]:
                if col in df_fallback.columns:
                    df_fallback[col] = pd.to_datetime(df_fallback[col])
            return df_fallback
        return None
    if df is None or df.empty:
        print("  WARNING: API returned no data.")
        return df

    if path.exists():
        print("  merging new data with existing historical data...")
        df_old = pd.read_csv(path, low_memory=False)
        for col in ["interval", "commissioning_date", "closure_date", "commenced", "retired"]:
            if col in df_old.columns:
                df_old[col] = pd.to_datetime(df_old[col])
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        combined = pd.concat([df_old, df], ignore_index=True)
        if "interval" in combined.columns:
            subset_cols = [c for c in combined.columns if c not in ["value", "price"]]
            combined = combined.drop_duplicates(subset=subset_cols, keep="last")
            combined = combined.sort_values("interval")
        else:
            subset_cols = [c for c in ["code", "unit_code", "facility_code"] if c in combined.columns]
            if subset_cols:
                combined = combined.drop_duplicates(subset=subset_cols, keep="last")
            else:
                combined = combined.drop_duplicates(keep="last")
        df = combined.copy()

    df.to_csv(path, index=False)
    summarize(path, df)
    return df


def pivot_to_wide(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot long-format fueltech data into wide format matching master CSV headers.

    Expects a DataFrame with columns: interval, value, metric, fueltech (at minimum).
    Returns a DataFrame indexed by 'date' with one column per fueltech+metric.
    """
    if df.empty or "fueltech" not in df.columns:
        return pd.DataFrame()

    # Build a mapping from (metric, fueltech) → wide column name.
    def _col_name(row):
        ft = row.get("fueltech")
        metric = str(row.get("metric", ""))
        if metric == "power":
            return FUELTECH_POWER_COLS.get(ft)
        elif metric == "emissions":
            return FUELTECH_EMISSIONS_COLS.get(ft)
        return None

    work = df[["interval", "value", "metric", "fueltech"]].copy()
    work["col_name"] = work.apply(_col_name, axis=1)
    work = work.dropna(subset=["col_name"])

    if work.empty:
        return pd.DataFrame()

    wide = work.pivot_table(
        index="interval", columns="col_name", values="value", aggfunc="mean"
    )
    wide.columns.name = None  # remove the "col_name" label
    wide = wide.reset_index().rename(columns={"interval": "date"})
    return wide


def append_to_master(master_path: Path, new_df: pd.DataFrame, label: str) -> None:
    """Append new wide-format data to an existing master CSV file.

    Deduplicates on the 'date' column (keeping most recent data) and sorts.
    Preserves any columns in the master file that are not present in new_df.
    """
    if new_df.empty:
        print(f"  [{label}] no new data to append.")
        return

    new_df["date"] = pd.to_datetime(new_df["date"])
    if new_df["date"].dt.tz is not None:
        new_df["date"] = new_df["date"].dt.tz_localize(None)

    if master_path.exists():
        print(f"  [{label}] reading existing master file...")
        master = pd.read_csv(master_path, low_memory=False)
        master["date"] = pd.to_datetime(master["date"])
        if master["date"].dt.tz is not None:
            master["date"] = master["date"].dt.tz_localize(None)
        combined = pd.concat([master, new_df], ignore_index=True)
    else:
        print(f"  [{label}] creating new master file...")
        combined = new_df.copy()

    combined = combined.drop_duplicates(subset=["date"], keep="last")
    combined = combined.sort_values("date").reset_index(drop=True)
    combined.to_csv(master_path, index=False)
    summarize(master_path, combined)
    print(f"  [{label}] master file updated: {len(combined):,} total rows.")


# --------------------------------------------------------------------------- #
# Dataset fetchers
# --------------------------------------------------------------------------- #
def main() -> int:
    now = nem_now()
    # Desired start is 2020-01-01, but the COMMUNITY plan clamps to ~730 days.
    desired_start = datetime(2020, 1, 1)
    plan_start = now - timedelta(days=MAX_HISTORY_DAYS)
    history_start = max(desired_start, plan_start)
    if history_start > desired_start:
        print(
            f"NOTE: plan history limit — clamping long-range start from "
            f"{desired_start:%Y-%m-%d} to {history_start:%Y-%m-%d} "
            f"(only last {MAX_HISTORY_DAYS} days available)."
        )

    with OEClient() as client:

        # ================================================================== #
        # Master file update: NEM (power + emissions + price, 7 days, 5 min)
        # ================================================================== #
        nem_master = RAW_DIR / "master_NEM_open_electricity.csv"
        print(f"\n[NEM master] -> {nem_master.name}")
        if cache_is_fresh(nem_master, max_age_h=0.083):
            print(f"  cache hit (< 0.083h old), skipping NEM master update.")
        else:
            try:
                print("  fetching NEM power + emissions (fueltech, 5m, 7d)...")
                resp_gen = client.get_network_data(
                    network_code="NEM",
                    metrics=[DataMetric.POWER, DataMetric.EMISSIONS],
                    interval="5m",
                    date_start=now - timedelta(days=7),
                    date_end=now,
                    secondary_grouping="fueltech",
                )
                df_gen = timeseries_to_df(resp_gen)
                print(f"  fetched {len(df_gen):,} generation/emissions rows.")

                print("  fetching NEM price (5m, 7d)...")
                resp_price = client.get_market(
                    network_code="NEM",
                    metrics=[MarketMetric.PRICE],
                    interval="5m",
                    date_start=now - timedelta(days=7),
                    date_end=now,
                )
                df_price = timeseries_to_df(resp_price)
                print(f"  fetched {len(df_price):,} price rows.")

                # Pivot generation data to wide format.
                wide = pivot_to_wide(df_gen)

                # Add price column.
                if not df_price.empty:
                    price_wide = (
                        df_price[["interval", "value"]]
                        .rename(columns={"interval": "date", "value": "Price - AUD/MWh"})
                    )
                    price_wide["date"] = pd.to_datetime(price_wide["date"])
                    if not wide.empty:
                        wide["date"] = pd.to_datetime(wide["date"])
                        wide = wide.merge(price_wide, on="date", how="outer")
                    else:
                        wide = price_wide

                append_to_master(nem_master, wide, "NEM master")
            except Exception as exc:  # noqa: BLE001
                print(f"  NEM MASTER FETCH FAILED: {type(exc).__name__}: {exc}")

        # ================================================================== #
        # Master file update: WEM / WA SWIS (power + emissions + price, 7d)
        # ================================================================== #
        wem_master = RAW_DIR / "master_WA_SWIS_open_electricity.csv"
        print(f"\n[WEM master] -> {wem_master.name}")
        if cache_is_fresh(wem_master, max_age_h=0.083):
            print(f"  cache hit (< 0.083h old), skipping WEM master update.")
        else:
            try:
                print("  fetching WEM power + emissions (fueltech, 5m, 7d)...")
                resp_gen_wem = client.get_network_data(
                    network_code="WEM",
                    metrics=[DataMetric.POWER, DataMetric.EMISSIONS],
                    interval="5m",
                    date_start=now - timedelta(days=7),
                    date_end=now,
                    secondary_grouping="fueltech",
                )
                df_gen_wem = timeseries_to_df(resp_gen_wem)
                print(f"  fetched {len(df_gen_wem):,} WEM generation/emissions rows.")

                print("  fetching WEM price (5m, 7d)...")
                resp_price_wem = client.get_market(
                    network_code="WEM",
                    metrics=[MarketMetric.PRICE],
                    interval="5m",
                    date_start=now - timedelta(days=7),
                    date_end=now,
                )
                df_price_wem = timeseries_to_df(resp_price_wem)
                print(f"  fetched {len(df_price_wem):,} WEM price rows.")

                wide_wem = pivot_to_wide(df_gen_wem)

                if not df_price_wem.empty:
                    price_wide_wem = (
                        df_price_wem[["interval", "value"]]
                        .rename(columns={"interval": "date", "value": "Price - AUD/MWh"})
                    )
                    price_wide_wem["date"] = pd.to_datetime(price_wide_wem["date"])
                    if not wide_wem.empty:
                        wide_wem["date"] = pd.to_datetime(wide_wem["date"])
                        wide_wem = wide_wem.merge(price_wide_wem, on="date", how="outer")
                    else:
                        wide_wem = price_wide_wem

                append_to_master(wem_master, wide_wem, "WEM master")
            except Exception as exc:  # noqa: BLE001
                print(f"  WEM MASTER FETCH FAILED: {type(exc).__name__}: {exc}")

        # --- Dataset B: annual generation by fuel, 2020->now, 1M, fueltech_group
        def fetch_b():
            resp = client.get_network_data(
                network_code="NEM",
                metrics=[DataMetric.ENERGY],
                interval="1M",
                date_start=history_start,
                date_end=now,
                secondary_grouping="fueltech_group",
            )
            return timeseries_to_df(resp)

        fetch_cached(RAW_DIR / "nem_annual_fuel_mix.csv", "B annual fuel mix", fetch_b)

        # --- Dataset C: per-state generation, past 12 months, 1M, region + fueltech_group
        def fetch_c():
            resp = client.get_network_data(
                network_code="NEM",
                metrics=[DataMetric.ENERGY],
                interval="1M",
                date_start=now - timedelta(days=365),
                date_end=now,
                primary_grouping="network_region",
                secondary_grouping="fueltech_group",
            )
            return timeseries_to_df(resp)

        fetch_cached(RAW_DIR / "nem_state_fuel_mix.csv", "C state fuel mix", fetch_c)

        # --- Dataset D: renewable share evolution, 2020->now, 1M, region + renewable flag
        def fetch_d():
            resp = client.get_network_data(
                network_code="NEM",
                metrics=[DataMetric.ENERGY],
                interval="1M",
                date_start=history_start,
                date_end=now,
                primary_grouping="network_region",
                secondary_grouping="renewable",
            )
            return timeseries_to_df(resp)

        fetch_cached(RAW_DIR / "nem_renewable_share.csv", "D renewable share", fetch_d)

        # --- Dataset E: coal facilities (incl. retirement dates from unit metadata)
        def fetch_e():
            resp = client.get_facilities(
                network_id=["NEM"],
                fueltech_id=["coal_black", "coal_brown"],
            )
            records = []
            for fac in resp.data:
                region = getattr(fac, "network_region", None)
                for unit in getattr(fac, "units", []) or []:
                    records.append(
                        {
                            "facility_code": fac.code,
                            "facility_name": fac.name,
                            "network_region": region,
                            "unit_code": getattr(unit, "code", None),
                            "fueltech": str(getattr(unit, "fueltech_id", None)),
                            "status": str(getattr(unit, "status_id", None)),
                            "capacity_mw": getattr(unit, "capacity_registered", None),
                            "commenced": getattr(unit, "commencement_date", None)
                            or getattr(unit, "data_first_seen", None),
                            "retired": getattr(unit, "closure_date", None)
                            or getattr(unit, "expected_closure_date", None)
                            or getattr(unit, "data_last_seen", None),
                        }
                    )
            return pd.DataFrame(records)

        fetch_cached(RAW_DIR / "nem_coal_facilities.csv", "E coal facilities", fetch_e)

    print("\nDone fetching all datasets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
