import nemosis
import pandas as pd

def main():
    start_time = "2026/05/01 00:00:00"
    end_time = "2026/05/02 00:00:00"
    
    print("Fetching DISPATCHPRICE...")
    dp = nemosis.dynamic_data_compiler(
        start_time, end_time, "DISPATCHPRICE", "./nemosis_cache"
    )
    print(dp.columns)
    print(dp.head())

if __name__ == "__main__":
    main()
