import pandas as pd
import nemosis
import os

cache_dir = "/home/jonathan/hdrenewable_int/data/nemosis_cache"
os.makedirs(cache_dir, exist_ok=True)

print("Fetching DISPATCHPRICE...")
dp = nemosis.dynamic_data_compiler("2023/11/01 00:00:00", "2023/12/31 00:00:00", "DISPATCHPRICE", cache_dir)
print("Fetching DISPATCHREGIONSUM...")
ds = nemosis.dynamic_data_compiler("2023/11/01 00:00:00", "2023/12/31 00:00:00", "DISPATCHREGIONSUM", cache_dir)

dp["SETTLEMENTDATE"] = pd.to_datetime(dp["SETTLEMENTDATE"])
ds["SETTLEMENTDATE"] = pd.to_datetime(ds["SETTLEMENTDATE"])

df = pd.DataFrame()
df["date"] = dp["SETTLEMENTDATE"].dt.date.unique()

dp["RAISE6SECRRP"] = pd.to_numeric(dp["RAISE6SECRRP"], errors="coerce")
ds["RAISE6SECLOCALDISPATCH"] = pd.to_numeric(ds["RAISE6SECLOCALDISPATCH"], errors="coerce")

print("\n--- Summary Statistics (Nov - Dec 2023) ---")
print("RAISE6SECRRP Daily Mean Price:")
daily_price = dp.groupby(dp["SETTLEMENTDATE"].dt.date)["RAISE6SECRRP"].mean()
print(daily_price.describe())
print("\nPrice on Nov 19:", daily_price[pd.to_datetime("2023-11-19").date()])
print("Price on Nov 20:", daily_price[pd.to_datetime("2023-11-20").date()])
print("Price on Nov 21:", daily_price[pd.to_datetime("2023-11-21").date()])
print("Price on Nov 22:", daily_price[pd.to_datetime("2023-11-22").date()])
print("Price on Nov 30:", daily_price[pd.to_datetime("2023-11-30").date()])

print("\nRAISE6SECLOCALDISPATCH Daily Mean Volume:")
daily_vol = ds.groupby(ds["SETTLEMENTDATE"].dt.date)["RAISE6SECLOCALDISPATCH"].mean()
print(daily_vol.describe())
print("\nVolume on Nov 19:", daily_vol[pd.to_datetime("2023-11-19").date()])
print("Volume on Nov 20:", daily_vol[pd.to_datetime("2023-11-20").date()])
print("Volume on Nov 21:", daily_vol[pd.to_datetime("2023-11-21").date()])

print("\nAre there missing intervals? (Count of intervals per day in DP)")
count_dp = dp.groupby(dp["SETTLEMENTDATE"].dt.date).size()
print(count_dp[count_dp < 1400]) # 288 * 5 regions = 1440

