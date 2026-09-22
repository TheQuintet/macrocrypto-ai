# run this file to create a corrected proxy dataset for the BAMLH0A0HYM2 series using HYG and SHY ETFs
# for the period from 2021-03-19 to 2023-09-18, and save it as a CSV in the scripts folder.


import os
import pandas as pd
import yfinance as yf

print("Fetching HYG and SHY data for the proxy gap...")

# Fetch cleanly as flat series
hyg = yf.download("HYG", start="2021-03-19", end="2023-09-18", progress=False)["Close"]
shy = yf.download("SHY", start="2021-03-19", end="2023-09-18", progress=False)["Close"]

# Ensure they are treated as 1D pandas Series even if returned as dataframes
if isinstance(hyg, pd.DataFrame):
    hyg = hyg.iloc[:, 0]
if isinstance(shy, pd.DataFrame):
    shy = shy.iloc[:, 0]

# Combine into a working dataframe safely
proxy_df = pd.DataFrame({"HYG": hyg, "SHY": shy}).dropna()

# 1. Calculate an inverse price ratio to model credit stress
raw_ratio = proxy_df["SHY"] / proxy_df["HYG"]

# 2. Scale into the historical BAMLH0A0HYM2 range (~3.0% to ~6.0%)
min_r, max_r = raw_ratio.min(), raw_ratio.max()
scaled_spread = 3.0 + ((raw_ratio - min_r) / (max_r - min_r)) * 3.0

# Format precisely to match your structure (Date index, float rounded to 2 decimals)
final_output = pd.DataFrame(index=proxy_df.index)
final_output["BAMLH0A0HYM2"] = scaled_spread.round(2)

# Save to your local scripts folder
output_path = "app/scripts/high_yield_spread_proxy.csv"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
final_output.to_csv(output_path)

print(f"Corrected proxy dataset saved to: {output_path}")
print(final_output.head())