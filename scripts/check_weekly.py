import pandas as pd

df = pd.read_csv("/home/jonathan/hdrenewable_int/data/raw/fcas_contingency.csv", parse_dates=["interval"])
df = df.sort_values("interval")

df_weekly = df.resample("W-MON", on="interval").sum(numeric_only=True).reset_index()
df_weekly["total_value"] = df_weekly[["fast_raise", "slow_raise", "delayed_raise", "fast_lower", "slow_lower", "delayed_lower"]].sum(axis=1)

print(df_weekly[(df_weekly["interval"] >= "2023-10-01") & (df_weekly["interval"] <= "2023-12-31")][["interval", "total_value", "fast_raise"]])
