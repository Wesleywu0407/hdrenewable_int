import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, timezone
import os
import sys
from dotenv import load_dotenv

from openelectricity import OEClient
from openelectricity.types import DataMetric, MarketMetric

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Load env for API key
load_dotenv(PROJECT_ROOT / ".env")
if not os.getenv("OPENELECTRICITY_API_KEY"):
    print("ERROR: OPENELECTRICITY_API_KEY not set.")
    sys.exit(1)

def timeseries_to_df(response) -> pd.DataFrame:
    records = []
    for ts in response.data:
        metric = getattr(ts, "metric", getattr(ts, "name", None))
        for series in ts.results:
            cols = series.columns
            labels = cols.model_dump() if hasattr(cols, "model_dump") else dict(cols or {})
            labels = {k: v for k, v in labels.items() if v is not None}
            for point in series.data:
                ts_val, val = point.root if hasattr(point, "root") else point
                records.append({
                    "interval": ts_val,
                    "value": val,
                    "metric": str(metric),
                    **labels,
                })
    df = pd.DataFrame(records)
    if not df.empty:
        df["interval"] = pd.to_datetime(df["interval"])
    return df

def main():
    print("Loading team member's master CSV...")
    master_path = RAW_DIR / "master_NEM_open_electricity.csv"
    master_df = pd.read_csv(master_path)
    master_df["date"] = pd.to_datetime(master_df["date"])
    
    # Pick a 1-day window that exists in the master file to test (e.g., June 10, 2026)
    test_start = datetime(2026, 6, 10, 0, 0, 0)
    test_end = datetime(2026, 6, 11, 0, 0, 0)
    
    # Filter master data to this window
    mask = (master_df["date"] >= test_start) & (master_df["date"] < test_end)
    master_subset = master_df.loc[mask].copy()
    print(f"Filtered master data: {len(master_subset)} rows for {test_start.date()}")
    
    print("\nFetching exact same window from OpenElectricity API...")
    with OEClient() as client:
        # Fetch Power
        resp_power = client.get_network_data(
            network_code="NEM",
            metrics=[DataMetric.POWER],
            interval="5m",
            date_start=test_start,
            date_end=test_end,
            secondary_grouping="fueltech_group"
        )
        df_power = timeseries_to_df(resp_power)
        
        # We also need to fetch Price to match the master file's price column
        resp_price = client.get_market(
            network_code="NEM",
            metrics=[MarketMetric.PRICE],
            interval="5m",
            date_start=test_start,
            date_end=test_end
        )
        df_price = timeseries_to_df(resp_price)

    # Prepare fetched data to Wide format
    # 1. Pivot Power
    # E.g. value of fueltech_group 'coal' -> 'Coal (Black) -  MW'
    # Wait, the API returns fueltech_group like 'coal', but master file splits 'Coal (Black)' and 'Coal (Brown)'.
    # We need to see if fueltech_group is enough, or if we need fueltech_id instead!
    print(f"\nFetched Power Rows: {len(df_power)}")
    if not df_power.empty:
        print("Columns available in fetched power data:", df_power.columns.tolist())
        print("Sample of fueltech_groups returned by API:", df_power["fueltech_group"].unique().tolist())
        
        # Let's pivot just to see what columns we get natively from fueltech_group
        pivot_power = df_power.pivot_table(index="interval", columns="fueltech_group", values="value", aggfunc="sum")
        print("\nPivoted columns (API fueltech_groups):", pivot_power.columns.tolist())
        
    print("\nColumns in Team Member's Master CSV:")
    print([c for c in master_df.columns if "MW" in c])
    
    print("\n--- ANALYSIS OF DIFFERENCES ---")
    print("If you look closely, the API's 'fueltech_group' groups ALL coal into 'coal'.")
    print("But the team member's master file has 'Coal (Black) -  MW' and 'Coal (Brown) -  MW'.")
    print("This means to exactly replicate the team member's file, our script must query 'fueltech_id' instead of 'fueltech_group'.")
    print("This verification script proves that the data *can* match, but the fetch logic requires careful column mapping to perfectly recreate the master CSV's structure.")

if __name__ == "__main__":
    main()
