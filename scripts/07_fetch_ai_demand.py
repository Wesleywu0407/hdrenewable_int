#!/usr/bin/env python3
"""
Generate synthetic data for AI Data Center Power Demand vs Renewable Supply projections.
This script creates a mock dataset (2025-2035) to model the "Green Energy Deficit".
"""

import os
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "raw"

def generate_projections() -> pd.DataFrame:
    years = np.arange(2025, 2036)
    
    # Base renewable supply growth (linear with slight acceleration)
    base_renewable_supply_mw = 15000
    renewable_growth_rate = 1500 # MW per year initially
    
    # AI Data Center demand (exponential growth)
    base_ai_demand_mw = 800
    ai_growth_factor = 1.35 # 35% growth YoY
    
    # Baseline grid demand (slow steady growth)
    base_grid_demand_mw = 25000
    grid_growth_rate = 200 # MW per year
    
    records = []
    
    for i, year in enumerate(years):
        # Calculate values
        renewable_supply = base_renewable_supply_mw + (renewable_growth_rate * i) + (50 * i**2)
        ai_demand = base_ai_demand_mw * (ai_growth_factor ** i)
        grid_demand = base_grid_demand_mw + (grid_growth_rate * i)
        
        total_demand = grid_demand + ai_demand
        
        # The deficit is the gap between total demand and renewable supply
        deficit = max(0, total_demand - renewable_supply)
        
        records.append({
            "Year": year,
            "Renewable_Supply_MW": round(renewable_supply, 2),
            "Baseline_Grid_Demand_MW": round(grid_demand, 2),
            "AI_Data_Center_Demand_MW": round(ai_demand, 2),
            "Total_Demand_MW": round(total_demand, 2),
            "Green_Energy_Deficit_MW": round(deficit, 2)
        })
        
    return pd.DataFrame(records)

def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / "ai_demand_projections.csv"
    
    print(f"Generating synthetic AI demand projections...")
    df = generate_projections()
    
    df.to_csv(out_path, index=False)
    print(f"Saved projections to {out_path}")
    print(df.head(11))

if __name__ == "__main__":
    main()
