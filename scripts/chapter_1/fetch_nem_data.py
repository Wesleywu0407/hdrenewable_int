"""Step 1 - Fetch all NEM data needed for the 4 charts.

Pulls datasets from the OpenElectricity API and caches each as CSV under
data/raw/. If a cache file exists and is < 24h old, the API call is skipped.

Run: python -m scripts.chapter_1.fetch_nem_data
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError

import pandas as pd
from dotenv import load_dotenv

from scripts.common.api import (
    DEFAULT_FETCH_EXCEPTIONS,
    cache_is_fresh,
    configure_logging,
    fetch_cached,
    summarize,
)
from scripts.common.constants import (
    FUELTECH_EMISSIONS_COLS,
    FUELTECH_POWER_COLS,
    NEM_REGIONS,
    NEM_TZ,
    WEM_TZ,
)
from scripts.common.paths import PROJECT_ROOT, RAW_DIR

LOGGER = logging.getLogger(__name__)
API_FETCH_EXCEPTIONS = (HTTPError, URLError, *DEFAULT_FETCH_EXCEPTIONS)

# COMMUNITY plan only exposes ~the last 730 days of history, and the 1M interval
# is capped at a 732-day range per request. We clamp long-range queries to this
# window. NOTE: this means 2020-2023 data is NOT available on this plan - the
# 5-year deliverables (Fig 2, Fig 4) are limited to the last ~2 years.
MAX_HISTORY_DAYS = 728


def setup_env() -> None:
    """Load environment settings and validate the OpenElectricity API key."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("OPENELECTRICITY_API_KEY")
    if not api_key or api_key.startswith("<"):
        LOGGER.error("OPENELECTRICITY_API_KEY not set in .env.")
        raise SystemExit(1)


def nem_now() -> datetime:
    """Current time in NEM network time, as a naive datetime for the API."""
    return datetime.now(NEM_TZ).replace(tzinfo=None)


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
            # rather than in the columns model - recover it when missing.
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
        df["interval"] = pd.to_datetime(df["interval"], utc=True)
    return df


def pivot_to_wide(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot long-format fueltech data into wide format matching master CSV headers.

    Expects a DataFrame with columns: interval, value, metric, fueltech (at minimum).
    Returns a DataFrame indexed by 'date' with one column per fueltech+metric.
    """
    if df.empty or "fueltech" not in df.columns:
        return pd.DataFrame()

    # Build a mapping from (metric, fueltech) to wide column name.
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

    # Fill small API gaps (e.g., 30-minute rooftop solar intervals in a 5-minute dataset)
    # method='time' ensures linear interpolation across timestamps. limit=6 covers 30 mins.
    wide = wide.interpolate(method="time", limit=6)

    wide.columns.name = None  # remove the "col_name" label
    wide = wide.reset_index().rename(columns={"interval": "date"})
    return wide


def append_to_master(master_path: Path, new_df: pd.DataFrame, label: str) -> None:
    """Append new wide-format data to an existing master CSV file.

    Deduplicates on the 'date' column (keeping most recent data) and sorts.
    Preserves any columns in the master file that are not present in new_df.
    """
    if new_df.empty:
        LOGGER.info("  [%s] no new data to append.", label)
        return

    new_df["date"] = pd.to_datetime(new_df["date"])
    if new_df["date"].dt.tz is not None:
        new_df["date"] = new_df["date"].dt.tz_localize(None)

    if master_path.exists():
        LOGGER.info("  [%s] reading existing master file...", label)
        master = pd.read_csv(master_path, low_memory=False)
        master["date"] = pd.to_datetime(master["date"])
        if master["date"].dt.tz is not None:
            master["date"] = master["date"].dt.tz_localize(None)

        master = master.set_index("date")
        new_idx = new_df.set_index("date")

        # Combine new data with old data.
        # new_idx.combine_first(master) prioritizes new_idx, but if new_idx has NaNs,
        # it fills them with values from master. This prevents API gaps from overwriting good data.
        combined = new_idx.combine_first(master).reset_index()
    else:
        LOGGER.info("  [%s] creating new master file...", label)
        combined = new_df.copy()

    combined = combined.sort_values("date").reset_index(drop=True)
    combined.to_csv(master_path, index=False)
    summarize(master_path, combined, logger=LOGGER)
    LOGGER.info("  [%s] master file updated: %s total rows.", label, f"{len(combined):,}")


# --------------------------------------------------------------------------- #
# Dataset fetchers
# --------------------------------------------------------------------------- #
def history_start_for(now: datetime) -> datetime:
    """Return the allowed historical query start for the current API plan."""
    desired_start = datetime(2020, 1, 1)
    plan_start = now - timedelta(days=MAX_HISTORY_DAYS)
    history_start = max(desired_start, plan_start)
    if history_start > desired_start:
        LOGGER.info(
            "NOTE: plan history limit - clamping long-range start from %s to %s "
            "(only last %s days available).",
            f"{desired_start:%Y-%m-%d}",
            f"{history_start:%Y-%m-%d}",
            MAX_HISTORY_DAYS,
        )
    return history_start


def fetch_network_master(
    client,
    data_metric,
    market_metric,
    *,
    network_code: str,
    label: str,
    local_tz,
    now: datetime,
) -> None:
    """Refresh a wide master file for power, emissions, and price."""
    master_path = RAW_DIR / (
        "master_NEM_open_electricity.csv"
        if network_code == "NEM"
        else "master_WA_SWIS_open_electricity.csv"
    )
    LOGGER.info("")
    LOGGER.info("[%s] -> %s", label, master_path.name)
    if cache_is_fresh(master_path, max_age_h=0):
        LOGGER.info("  cache hit, skipping %s update.", label)
        return

    try:
        LOGGER.info("  fetching %s power + emissions (fueltech, 5m, 7d)...", network_code)
        resp_gen = client.get_network_data(
            network_code=network_code,
            metrics=[data_metric.POWER, data_metric.EMISSIONS],
            interval="5m",
            date_start=now - timedelta(days=7),
            date_end=now,
            secondary_grouping="fueltech",
        )
        df_gen = timeseries_to_df(resp_gen)
        LOGGER.info("  fetched %s generation/emissions rows.", f"{len(df_gen):,}")

        LOGGER.info("  fetching %s price (5m, 7d)...", network_code)
        resp_price = client.get_market(
            network_code=network_code,
            metrics=[market_metric.PRICE],
            interval="5m",
            date_start=now - timedelta(days=7),
            date_end=now,
        )
        df_price = timeseries_to_df(resp_price)
        LOGGER.info("  fetched %s price rows.", f"{len(df_price):,}")

        if not df_gen.empty:
            df_gen["interval"] = df_gen["interval"].dt.tz_convert(local_tz).dt.tz_localize(None)
        if not df_price.empty:
            df_price["interval"] = df_price["interval"].dt.tz_convert(local_tz).dt.tz_localize(None)

        wide = pivot_to_wide(df_gen)
        if not df_price.empty:
            price_wide = df_price[["interval", "value"]].rename(
                columns={"interval": "date", "value": "Price - AUD/MWh"}
            )
            price_wide["date"] = pd.to_datetime(price_wide["date"])
            if not wide.empty:
                wide["date"] = pd.to_datetime(wide["date"])
                wide = wide.merge(price_wide, on="date", how="outer")
            else:
                wide = price_wide

        append_to_master(master_path, wide, label)
    except API_FETCH_EXCEPTIONS as exc:
        LOGGER.error("  %s FETCH FAILED: %s: %s", label.upper(), type(exc).__name__, exc)


def fetch_annual_fuel_mix(client, data_metric, now: datetime, history_start: datetime) -> None:
    """Fetch NEM annual/monthly fuel mix data."""
    def fetch() -> pd.DataFrame:
        resp = client.get_network_data(
            network_code="NEM",
            metrics=[data_metric.ENERGY],
            interval="1M",
            date_start=history_start,
            date_end=now,
            secondary_grouping="fueltech_group",
        )
        df = timeseries_to_df(resp)
        if not df.empty:
            df["interval"] = df["interval"].dt.tz_convert(NEM_TZ).dt.tz_localize(None)
        return df

    fetch_cached(
        RAW_DIR / "nem_annual_fuel_mix.csv",
        "B annual fuel mix",
        fetch,
        exceptions=API_FETCH_EXCEPTIONS,
        logger=LOGGER,
    )


def fetch_state_fuel_mix(client, data_metric, now: datetime) -> None:
    """Fetch per-state generation by fueltech group."""
    def fetch() -> pd.DataFrame:
        resp = client.get_network_data(
            network_code="NEM",
            metrics=[data_metric.ENERGY],
            interval="1M",
            date_start=now - timedelta(days=365),
            date_end=now,
            primary_grouping="network_region",
            secondary_grouping="fueltech_group",
        )
        df = timeseries_to_df(resp)
        if not df.empty:
            df["interval"] = df["interval"].dt.tz_convert(NEM_TZ).dt.tz_localize(None)
        return df

    fetch_cached(
        RAW_DIR / "nem_state_fuel_mix.csv",
        "C state fuel mix",
        fetch,
        exceptions=API_FETCH_EXCEPTIONS,
        logger=LOGGER,
    )


def fetch_renewable_share(client, data_metric, now: datetime, history_start: datetime) -> None:
    """Fetch renewable share by region."""
    def fetch() -> pd.DataFrame:
        resp = client.get_network_data(
            network_code="NEM",
            metrics=[data_metric.ENERGY],
            interval="1M",
            date_start=history_start,
            date_end=now,
            primary_grouping="network_region",
            secondary_grouping="renewable",
        )
        df = timeseries_to_df(resp)
        if not df.empty:
            df["interval"] = df["interval"].dt.tz_convert(NEM_TZ).dt.tz_localize(None)
        return df

    fetch_cached(
        RAW_DIR / "nem_renewable_share.csv",
        "D renewable share",
        fetch,
        exceptions=API_FETCH_EXCEPTIONS,
        logger=LOGGER,
    )


def fetch_coal_facilities(client) -> None:
    """Fetch coal facility metadata, including retirement dates."""
    def fetch() -> pd.DataFrame:
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

    fetch_cached(
        RAW_DIR / "nem_coal_facilities.csv",
        "E coal facilities",
        fetch,
        exceptions=API_FETCH_EXCEPTIONS,
        logger=LOGGER,
    )


def main() -> int:
    configure_logging()
    setup_env()

    from openelectricity import OEClient
    from openelectricity.types import DataMetric, MarketMetric

    now = nem_now()
    history_start = history_start_for(now)

    with OEClient() as client:
        fetch_network_master(
            client,
            DataMetric,
            MarketMetric,
            network_code="NEM",
            label="NEM master",
            local_tz=NEM_TZ,
            now=now,
        )
        fetch_network_master(
            client,
            DataMetric,
            MarketMetric,
            network_code="WEM",
            label="WEM master",
            local_tz=WEM_TZ,
            now=now,
        )
        fetch_annual_fuel_mix(client, DataMetric, now, history_start)
        fetch_state_fuel_mix(client, DataMetric, now)
        fetch_renewable_share(client, DataMetric, now, history_start)
        fetch_coal_facilities(client)

    LOGGER.info("")
    LOGGER.info("Done fetching all datasets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
