"""Chapter 1.1 Step 1 — Fetch & derive QLD-specific datasets.

Reuses cached Chapter 1.2 Parquet where possible and adds QLD drill-down data:
  - qld_facilities.parquet         : all QLD1 units (operating + retired)
  - qld_capacity_history.parquet   : derived monthly cumulative capacity per fueltech
  - peer_capacity_additions.parquet: QLD/NSW/VIC renewable additions per year (for Fig 4)
  - qld_spot_prices.parquet        : hourly QLD1 spot price, last 12 months (chunked)

Run: python scripts/03_fetch_qld_data.py
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(PROJECT_ROOT / ".env")
if not os.getenv("OPENELECTRICITY_API_KEY"):
    print("ERROR: OPENELECTRICITY_API_KEY not set in .env.")
    sys.exit(1)

from openelectricity import OEClient  # noqa: E402
from openelectricity.types import DataMetric, MarketMetric  # noqa: E402

CACHE_MAX_AGE_H = 24
NEM_TZ = timezone(timedelta(hours=10))

# Renewable generation fueltechs (storage handled separately).
RENEWABLE_FT = {
    "solar_utility",
    "solar_rooftop",
    "solar_thermal",
    "wind",
    "wind_offshore",
    "hydro",
    "bioenergy_biomass",
    "bioenergy_biogas",
}


def nem_now() -> datetime:
    return datetime.now(NEM_TZ).replace(tzinfo=None)


def cache_is_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    return (time.time() - path.stat().st_mtime) / 3600 < CACHE_MAX_AGE_H


def to_naive(ts) -> pd.Timestamp | None:
    if ts is None:
        return None
    t = pd.Timestamp(ts)
    return t.tz_localize(None) if t.tzinfo else t


# --------------------------------------------------------------------------- #
# Facility helpers
# --------------------------------------------------------------------------- #
def facilities_to_df(client: OEClient, region: str) -> pd.DataFrame:
    """Flatten all units in a region into a tidy facility/unit DataFrame."""
    resp = client.get_facilities(network_id=["NEM"], network_region=region)
    rows = []
    for f in resp.data:
        for u in f.units:
            rows.append(
                {
                    "name": f.name,
                    "code": f.code,
                    "unit_code": getattr(u, "code", None),
                    "network_region": region,
                    "fueltech": str(getattr(u, "fueltech_id", None)),
                    "status_id": str(getattr(u, "status_id", None)),
                    "capacity_registered": getattr(u, "capacity_registered", None),
                    "commissioning_date": to_naive(getattr(u, "commencement_date", None)),
                    "closure_date": to_naive(
                        getattr(u, "closure_date", None)
                        or getattr(u, "expected_closure_date", None)
                    ),
                }
            )
    return pd.DataFrame(rows)


def build_capacity_history(fac: pd.DataFrame) -> pd.DataFrame:
    """Monthly cumulative installed capacity (MW) per fueltech for one region.

    Adds capacity at commissioning, subtracts it at closure (when known).
    Units with no commissioning date are skipped (cannot be placed in time).
    """
    df = fac.dropna(subset=["commissioning_date", "capacity_registered"]).copy()
    if df.empty:
        return pd.DataFrame()
    start = df["commissioning_date"].min().to_period("M").to_timestamp()
    end = pd.Timestamp(nem_now()).to_period("M").to_timestamp()
    months = pd.date_range(start, end, freq="MS")

    out = []
    for ft, grp in df.groupby("fueltech"):
        for m in months:
            online = grp[
                (grp["commissioning_date"] <= m)
                & ((grp["closure_date"].isna()) | (grp["closure_date"] > m))
            ]
            out.append({"month": m, "fueltech": ft, "capacity_mw": online["capacity_registered"].sum()})
    return pd.DataFrame(out)


def build_peer_additions(facs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Renewable capacity added per calendar year, per state (for Fig 4)."""
    rows = []
    for region, fac in facs.items():
        df = fac[
            fac["fueltech"].isin(RENEWABLE_FT)
            & fac["commissioning_date"].notna()
            & fac["capacity_registered"].notna()
        ].copy()
        df["year"] = df["commissioning_date"].dt.year
        agg = df.groupby("year")["capacity_registered"].sum().reset_index()
        agg["network_region"] = region
        rows.append(agg)
    res = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    return res.rename(columns={"capacity_registered": "mw_added"})


# --------------------------------------------------------------------------- #
# Spot price (chunked: 1h interval capped at 32-day windows)
# --------------------------------------------------------------------------- #
def fetch_spot_prices(client: OEClient, region: str, days: int = 365) -> pd.DataFrame:
    now = nem_now()
    start = now - timedelta(days=days)
    rows = []
    window = timedelta(days=31)  # stay under the 32-day API cap
    cur = start
    while cur < now:
        chunk_end = min(cur + window, now)
        try:
            resp = client.get_market(
                network_code="NEM",
                metrics=[MarketMetric.PRICE],
                interval="1h",
                date_start=cur,
                date_end=chunk_end,
                network_region=region,
            )
            for ts in resp.data:
                for series in ts.results:
                    for point in series.data:
                        t, v = point.root if hasattr(point, "root") else point
                        rows.append({"interval": t, "price": v, "network_region": region})
        except Exception as exc:  # noqa: BLE001
            print(f"    price chunk {cur:%Y-%m-%d} failed: {type(exc).__name__}: {exc}")
        cur = chunk_end
    df = pd.DataFrame(rows)
    if not df.empty:
        df["interval"] = pd.to_datetime(df["interval"])
        df = df.drop_duplicates(subset=["interval"]).sort_values("interval")
    return df


def fetch_qld_fuel_mix(client: OEClient, months: int = 24) -> pd.DataFrame:
    """QLD1 monthly energy by fueltech_group over the last `months` months."""
    now = nem_now()
    # 1M interval is capped at a 732-day range; 24 months of daily-span would
    # exceed it, so clamp the start to 725 days back (~24 months).
    span_days = min(months * 31, 725)
    resp = client.get_network_data(
        network_code="NEM",
        metrics=[DataMetric.ENERGY],
        interval="1M",
        date_start=now - timedelta(days=span_days),
        date_end=now,
        network_region="QLD1",
        secondary_grouping="fueltech_group",
    )
    rows = []
    for ts in resp.data:
        for series in ts.results:
            cols = series.columns.model_dump()
            ft = cols.get("fueltech_group")
            for point in series.data:
                t, v = point.root if hasattr(point, "root") else point
                rows.append({"interval": t, "value": v, "fueltech_group": ft, "unit": ts.unit})
    df = pd.DataFrame(rows)
    if not df.empty:
        df["interval"] = pd.to_datetime(df["interval"])
    return df


def save_and_merge(path: Path, df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    if path.exists():
        print(f"  merging new data with existing historical data for {path.name}...")
        df_old = pd.read_csv(path, low_memory=False)
        for col in ["interval", "commissioning_date", "closure_date", "month"]:
            if col in df_old.columns:
                df_old[col] = pd.to_datetime(df_old[col])
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        combined = pd.concat([df_old, df], ignore_index=True)
        if "interval" in combined.columns:
            subset_cols = [c for c in combined.columns if c not in ["value", "price", "unit"]]
            combined = combined.drop_duplicates(subset=subset_cols, keep="last")
            combined = combined.sort_values("interval")
        elif "month" in combined.columns:
            subset_cols = [c for c in combined.columns if c not in ["capacity_mw"]]
            combined = combined.drop_duplicates(subset=subset_cols, keep="last")
            combined = combined.sort_values("month")
        else:
            subset_cols = [c for c in ["code", "unit_code", "network_region", "year"] if c in combined.columns]
            if subset_cols:
                combined = combined.drop_duplicates(subset=subset_cols, keep="last")
            else:
                combined = combined.drop_duplicates(keep="last")
        df = combined.copy()
    df.to_csv(path, index=False)
    return df

def summarize(path: Path, df: pd.DataFrame, note: str = "") -> None:
    size_kb = path.stat().st_size / 1024
    print(f"  saved {path.name}: {len(df):,} rows, {size_kb:.1f} KB {note}")


# --------------------------------------------------------------------------- #
def main() -> int:
    with OEClient() as client:
        # --- QLD facilities ------------------------------------------------ #
        qld_path = RAW_DIR / "qld_facilities.csv"
        if cache_is_fresh(qld_path):
            qld = pd.read_csv(qld_path, low_memory=False)
            if "commissioning_date" in qld.columns:
                qld["commissioning_date"] = pd.to_datetime(qld["commissioning_date"])
            if "closure_date" in qld.columns:
                qld["closure_date"] = pd.to_datetime(qld["closure_date"])
            print(f"[qld_facilities] cache hit ({len(qld)} units).")
        else:
            print("[qld_facilities] fetching QLD1 ...")
            qld = facilities_to_df(client, "QLD1")
            qld = save_and_merge(qld_path, qld)
            summarize(qld_path, qld)
        cod_cov = qld["commissioning_date"].notna().mean() * 100
        print(f"  QLD units: {len(qld)} | commissioning-date coverage: {cod_cov:.0f}%")
        print(f"  status: {qld['status_id'].value_counts().to_dict()}")

        # --- Peer facilities (NSW, VIC) for Fig 4 -------------------------- #
        peers = {"QLD1": qld}
        for region in ["NSW1", "VIC1"]:
            print(f"[peer_facilities] fetching {region} ...")
            peers[region] = facilities_to_df(client, region)
            print(f"  {region}: {len(peers[region])} units")

        # --- Capacity history (QLD) ---------------------------------------- #
        ch_path = RAW_DIR / "qld_capacity_history.csv"
        cap_hist = build_capacity_history(qld)
        cap_hist = save_and_merge(ch_path, cap_hist)
        summarize(ch_path, cap_hist, f"({cap_hist['month'].min():%Y-%m}..{cap_hist['month'].max():%Y-%m})")

        # --- Peer additions per year --------------------------------------- #
        pa_path = RAW_DIR / "peer_capacity_additions.csv"
        peer_add = build_peer_additions(peers)
        peer_add = save_and_merge(pa_path, peer_add)
        summarize(pa_path, peer_add)

        # --- QLD 24-month fuel mix (Fig 2) --------------------------------- #
        fm_path = RAW_DIR / "qld_fuel_mix_24m.csv"
        if cache_is_fresh(fm_path):
            print(f"[qld_fuel_mix_24m] cache hit.")
        else:
            print("[qld_fuel_mix_24m] fetching QLD1 monthly fuel mix ...")
            fm = fetch_qld_fuel_mix(client, months=24)
            fm = save_and_merge(fm_path, fm)
            summarize(fm_path, fm, f"({fm['interval'].min():%Y-%m}..{fm['interval'].max():%Y-%m})")

        # --- QLD spot prices ----------------------------------------------- #
        sp_path = RAW_DIR / "qld_spot_prices.csv"
        if cache_is_fresh(sp_path):
            sp = pd.read_csv(sp_path, low_memory=False)
            if "interval" in sp.columns:
                sp["interval"] = pd.to_datetime(sp["interval"])
            print(f"[qld_spot_prices] cache hit ({len(sp)} hours).")
        else:
            print("[qld_spot_prices] fetching QLD1 hourly (chunked) ...")
            sp = fetch_spot_prices(client, "QLD1", days=365)
            if sp.empty:
                print("  WARNING: no spot price data returned — Fig 6 will be skipped.")
            else:
                sp = save_and_merge(sp_path, sp)
                summarize(sp_path, sp, f"({sp['interval'].min():%Y-%m-%d}..{sp['interval'].max():%Y-%m-%d})")
                neg = (sp["price"] < 0).sum()
                print(f"  negative-price hours: {neg} ({neg/len(sp)*100:.1f}% of {len(sp)})")

    print("\nDone fetching QLD data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
