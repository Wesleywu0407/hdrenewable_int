# HDRE & ZEBRE Projects Implementation Plan

This document outlines the end-to-end plan to integrate the missing HD Renewable Energy (HDRE) / ZEBRE joint venture projects into the infrastructure map, and to correct the incorrect data being pulled for the Templers BESS project. 

## Phase 1: Addressing the Templers BESS Data Issue

**The Issue:** The OpenElectricity API data feed currently reports the Templers BESS at an incorrect capacity of 414 MW. The verified capacity is 111 MW. 
**The Solution:** Implement a manual override mechanism in `scripts/07_fetch_infrastructure_data.py`. 

**Implementation Steps:**
1. Locate the data processing block where the `bess_df` (Battery Energy Storage Systems DataFrame) is consolidated from the various scraper functions.
2. Introduce a data cleaning / override step right before the dataframe is saved to `data/raw/bess_locations.csv`.
3. The logic will find the row where `name == "Templers"` (or specifically matching the OpenElectricity source entry).
4. Override the `capacity_mw` value for that row from `414.0` to `111.0`.

## Phase 2: Injecting Missing HDRE / ZEBRE Projects

**The Issue:** Several key HDRE/ZEBRE projects (Solar River, Noblevale, North Yarragon, Hookey Creek) and the BESS portion of Wagga North are currently missing from the map because they are not present in the scraped API sources.
**The Solution:** Create a function to inject these verified projects manually into the pipeline.

**Implementation Steps:**
1. In `scripts/07_fetch_infrastructure_data.py`, create a new function called `inject_hdre_manual_projects(bess_df, solar_df)`.
2. Hardcode the verified list of missing BESS and Solar projects into a dictionary or list format containing the exact columns expected by the pipeline: `["name", "state", "capacity_mw", "status", "lat", "lon", "source"]`.
3. The injected data will include:
    *   **Solar River Hybrid (SA):** 
        *   Solar: 210 MW (Lat/Lon: ~ -33.9, 139.7)
        *   BESS: 256 MW (Lat/Lon: ~ -33.9, 139.7)
    *   **Wagga North BESS (NSW):** 
        *   BESS: 105 MW *(Note: The 55 MW Solar portion is already scraped, so this only adds the BESS)* (Lat/Lon: ~ -35.07, 147.43)
    *   **North Yarragon BESS (VIC):**
        *   BESS: 210 MW (Lat/Lon: ~ -38.2, 146.0)
    *   **Noblevale BESS (QLD):**
        *   BESS: 180 MW (Lat/Lon: ~ -27.65, 152.8)
    *   **Hookey Creek Solar & Battery (QLD):**
        *   Solar: 100 MW (Lat/Lon: ~ -26.1, 152.4)
        *   BESS: 200 MW (Lat/Lon: ~ -26.1, 152.4)
    *(Note: Approximate latitudes/longitudes will be hardcoded based on the locations researched).*
4. Convert these hardcoded lists into Pandas DataFrames.
5. Use `pd.concat()` to append these manual dataframes to the master `bess_df` and `solar_df` inside the main execution block of the script.

## Phase 3: Data Saving and Map Generation Validation

**Implementation Steps:**
1. Run the scraper script (`python scripts/07_fetch_infrastructure_data.py`) to execute the new overrides and injections.
2. Validate that `data/raw/bess_locations.csv` and `data/raw/solar_locations.csv` now contain the correct 111 MW value for Templers, and the new rows for the injected projects.
3. Check the dashboard or run the map generation script (`python scripts/08_generate_infrastructure_charts.py`) to ensure the Plotly maps successfully render the new markers.

## Phase 4: Updating Graph Descriptions and Sources

**The Issue:** The graph descriptions, UI legends, and source citations need to accurately reflect the manual addition of these HDRE/ZEBRE projects.
**The Solution:** Update the UI and chart configuration code to acknowledge the new data sources.

**Implementation Steps:**
1. In `scripts/08_generate_infrastructure_charts.py` or the `dashboard/app.py` UI rendering logic, locate where the data sources are described to the user (e.g., underneath the map or in tooltips).
2. Add "ZEBRE Joint Venture / HDRE verified data" (or similar wording) to the list of acknowledged sources for the map.
3. Ensure that the manually injected data points have their `source` column set to "HDRE/ZEBRE Verified Data" during Phase 2, so that on-hover tooltips on the map correctly attribute them.

## Phase 5: Auditing and Mitigating Data API Anomalies

**The Issue:** An analysis of the raw data outputs reveals systemic misattribution and inflation of capacities from the `OpenElectricity API` and `OpenStreetMap` sources. For example:
*   **Waratah Super Battery:** Listed as 3287 MW (Actual: 850 MW).
*   **Liddell & Eraring:** Listed as 2265 MW and 1843 MW BESS respectively, incorrectly inheriting the capacity limits of the retired/retiring coal plants instead of the actual BESS limits.
*   **Tomago:** Listed as 1500 MW (It is an aluminium smelter, not a battery).
*   **Oodnadatta Renewable Power Station (Solar):** Listed as 569 MW via OpenStreetMap (highly unlikely for a microgrid).

**The Solution:** Implement a robust validation or filtering mechanism for ingested third-party data to prevent these extreme outliers from skewing the map and analytics.

**Implementation Steps:**
1. In `scripts/07_fetch_infrastructure_data.py`, introduce a validation step after the OpenElectricity and OpenStreetMap data is fetched.
2. Filter out or flag extreme outliers (e.g., any single BESS with `capacity_mw > 1000` is highly suspect in the current market and should be dropped or manually verified).
3. Alternatively, cross-reference high-capacity entries against the AEMO Generation Information dataset, which is generally more reliable, and use AEMO's capacity figures if a discrepancy exists.
