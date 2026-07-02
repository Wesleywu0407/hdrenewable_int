import pandas as pd
import re
b = pd.read_csv("data/raw/bess_locations.csv")
s = pd.read_csv("data/raw/solar_locations.csv")
b_hdre = b[b.source.str.contains("ZEBRE", na=False)].copy()
b_hdre["asset_type"] = "Battery"
s_hdre = s[s.source.str.contains("ZEBRE", na=False)].copy()
s_hdre["asset_type"] = "Solar"
combined = pd.concat([b_hdre, s_hdre], ignore_index=True)
print("combined rows:", len(combined))
g = combined.groupby(["name", "lat", "lon", "status", "state", "source"], dropna=False)
print("groups:", len(g))
for n, grp in g:
    print(n, len(grp))
