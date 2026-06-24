import pandas as pd
import nemosis
import os

cache_dir = "/home/jonathan/hdrenewable_int/data/nemosis_cache"
os.makedirs(cache_dir, exist_ok=True)

print("Fetching DISPATCHPRICE...")
dp = nemosis.dynamic_data_compiler("2023/11/01 00:00:00", "2023/12/31 00:00:00", "DISPATCHPRICE", cache_dir)
print("Columns in DP:", dp.columns.tolist())

# Check if RAISE1SECRRP exists
if "RAISE1SECRRP" in dp.columns:
    dp["SETTLEMENTDATE"] = pd.to_datetime(dp["SETTLEMENTDATE"])
    dp["RAISE1SECRRP"] = pd.to_numeric(dp["RAISE1SECRRP"], errors="coerce")
    daily_1sec = dp.groupby(dp["SETTLEMENTDATE"].dt.date)["RAISE1SECRRP"].mean()
    print("\n--- RAISE1SECRRP Daily Mean Price ---")
    print("Nov 19:", daily_1sec.get(pd.to_datetime("2023-11-19").date(), "N/A"))
    print("Nov 20:", daily_1sec.get(pd.to_datetime("2023-11-20").date(), "N/A"))
    print("Nov 21:", daily_1sec.get(pd.to_datetime("2023-11-21").date(), "N/A"))
else:
    print("RAISE1SECRRP not in DISPATCHPRICE!")
