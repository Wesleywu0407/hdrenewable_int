import pandas as pd
import numpy as np
from pathlib import Path

def generate_state_infrastructure(raw_dir, output_dir):
    """
    Generate state-by-state actual infrastructure data:
    DC counts, BESS capacities, and Solar capacities.
    """
    # 1. Data Centres
    dc_df = pd.read_csv(raw_dir / 'datacentre_locations.csv')
    
    def infer_state(row):
        if pd.notnull(row.get('state')) and str(row.get('state')).strip() != '':
            return row['state']
        city_addr = str(row.get('city', '')) + ' ' + str(row.get('address', ''))
        city_addr = city_addr.lower()
        if 'nsw' in city_addr or 'sydney' in city_addr: return 'NSW'
        if 'vic' in city_addr or 'melbourne' in city_addr: return 'VIC'
        if 'qld' in city_addr or 'brisbane' in city_addr: return 'QLD'
        if 'wa' in city_addr or 'perth' in city_addr: return 'WA'
        if 'sa' in city_addr or 'adelaide' in city_addr: return 'SA'
        if 'act' in city_addr or 'canberra' in city_addr: return 'ACT'
        return 'Unknown'
        
    dc_df['state_inferred'] = dc_df.apply(infer_state, axis=1)
    dc_counts = dc_df.groupby('state_inferred').size().reset_index(name='dc_count')
    dc_counts = dc_counts.rename(columns={'state_inferred': 'state'})
    
    # 2. BESS
    bess_df = pd.read_csv(raw_dir / 'bess_locations.csv')
    bess_mw = bess_df.groupby('state')['capacity_mw'].sum().reset_index(name='bess_mw')
    
    # 3. Solar
    solar_df = pd.read_csv(raw_dir / 'solar_locations.csv')
    solar_mw = solar_df.groupby('state')['capacity_mw'].sum().reset_index(name='solar_mw')
    
    # Merge
    states = ['NSW', 'VIC', 'QLD', 'SA', 'WA', 'ACT', 'TAS']
    state_df = pd.DataFrame({'state': states})
    
    df = state_df.merge(dc_counts, on='state', how='left')\
                 .merge(bess_mw, on='state', how='left')\
                 .merge(solar_mw, on='state', how='left').fillna(0)
                 
    # Convert MW to GW for charts
    df['bess_gw'] = df['bess_mw'] / 1000.0
    df['solar_gw'] = df['solar_mw'] / 1000.0
    
    df.to_csv(output_dir / 'ch3_state_infrastructure.csv', index=False)
    print(f"Generated {output_dir / 'ch3_state_infrastructure.csv'}")

def generate_price_and_solar_profile(raw_dir, output_dir):
    """
    Generate hourly price, solar irradiance, and negative price events profile.
    """
    wpc = pd.read_csv(raw_dir / 'weather_price_correlation.csv')
    wpc['interval'] = pd.to_datetime(wpc['interval'])
    wpc['hour'] = wpc['interval'].dt.hour
    
    # Hourly averages
    hourly_avg = wpc.groupby('hour').agg({
        'price': 'mean',
        'direct_radiation': 'mean',
        'demand': 'mean'
    }).reset_index()
    
    # Negative events
    neg_events = wpc[wpc['price'] < 0].groupby('hour').size().reset_index(name='negative_events')
    
    # Merge
    profile = hourly_avg.merge(neg_events, on='hour', how='left').fillna(0)
    profile.to_csv(output_dir / 'ch3_hourly_profile.csv', index=False)
    print(f"Generated {output_dir / 'ch3_hourly_profile.csv'}")

def generate_bess_firming_case(raw_dir, output_dir):
    """
    Simulate a simplified firming case for a 100MW Data Centre.
    Compare cost of pulling from grid vs offset by 100MW BESS arbitrage.
    """
    wpc = pd.read_csv(raw_dir / 'weather_price_correlation.csv')
    wpc['interval'] = pd.to_datetime(wpc['interval'])
    wpc['date'] = wpc['interval'].dt.date
    wpc['hour'] = wpc['interval'].dt.hour
    
    # Daily costs
    # 100MW constant load means 100 MWh per hour
    # Grid cost = price * 100 (if price is negative, DC is paid)
    wpc['grid_cost'] = wpc['price'] * 100 
    
    daily_stats = wpc.groupby('date').agg({'grid_cost': 'sum', 'price': ['min', 'max']}).reset_index()
    daily_stats.columns = ['date', 'daily_grid_cost', 'min_price', 'max_price']
    
    # Simple 2-hour 100MW BESS (200MWh)
    # Charge at min price (200 MWh), discharge at max price (200 MWh)
    daily_stats['bess_arbitrage_revenue'] = (daily_stats['max_price'] - daily_stats['min_price']) * 200
    daily_stats['net_firmed_cost'] = daily_stats['daily_grid_cost'] - daily_stats['bess_arbitrage_revenue']
    
    daily_stats.to_csv(output_dir / 'ch3_firming_case.csv', index=False)
    print(f"Generated {output_dir / 'ch3_firming_case.csv'}")

if __name__ == '__main__':
    raw_dir = Path('data/raw')
    output_dir = Path('data/processed_ch3')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generate_state_infrastructure(raw_dir, output_dir)
    generate_price_and_solar_profile(raw_dir, output_dir)
    generate_bess_firming_case(raw_dir, output_dir)
    print("Real Chapter 3 ETL complete.")
