import os
import pandas as pd
from fredapi import Fred
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
FRED_API_KEY = os.getenv("FRED_API_KEY")

if not FRED_API_KEY:
    raise ValueError("FRED_API_KEY environment variable is missing. Please set it in your .env file.")

fred = Fred(api_key=FRED_API_KEY)

# Define the macroeconomic series to track
MACRO_SERIES = {
    "cpi": "CPIAUCSL",             # Consumer Price Index
    "unemployment": "UNRATE",      # Unemployment Rate
    "federal_funds_rate": "FEDFUNDS", # Federal Funds Rate
    "m2_money_supply": "M2SL",     # M2 Money Supply
    "gdp": "GDP"                   # Gross Domestic Product
}

def fetch_all_releases(series_id, name, start_date="2015-01-01"):
    print(f"[START] Beginning extraction for {name} ({series_id})...")
    try:
        print(f"[FETCHING] Querying FRED/ALFRED API for all releases of {series_id}...")
        # Gets a DataFrame with columns: 'date', 'realtime_start', 'value'
        df = fred.get_series_all_releases(series_id)
        
        # Filter by start date
        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"] >= pd.to_datetime(start_date)]
        
        df["series_id"] = series_id
        print(f"[DONE] Successfully fetched {len(df):,} records for {name}.")
        return df
    except Exception as e:
        print(f"[ERROR] Failed to fetch {series_id}: {e}")
        return None

def main():
    all_data = []
    record_counts = {}
    
    print("==================================================")
    print("       MACROECONOMIC VINTAGE INGESTION JOB        ")
    print("==================================================")
    
    for name, series_id in MACRO_SERIES.items():
        df = fetch_all_releases(series_id, name)
        if df is not None:
            df["feature_name"] = name
            all_data.append(df)
            record_counts[name] = len(df)
        else:
            record_counts[name] = 0
        print("-" * 50)
            
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        # Rename columns for clarity: 'date' = observation_date, 'realtime_start' = release_date
        combined_df = combined_df.rename(columns={"date": "observation_date", "realtime_start": "release_date"})
        
        output_path = "app/data/macro_raw_with_vintages.csv"
        os.makedirs("app/data", exist_ok=True)
        combined_df.to_csv(output_path, index=False)
        
        print("\n==================================================")
        print("          MACRO VINTAGE INGESTION SUMMARY         ")
        print("==================================================")
        for feature, count in record_counts.items():
            print(f"  * {feature.upper():<20} ({MACRO_SERIES[feature]}): {count:,} records")
        print("--------------------------------------------------")
        print(f"Saved combined vintage dataset to: {output_path}")
        print("==================================================")

if __name__ == "__main__":
    main()