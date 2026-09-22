"""
Download raw HYG and SHY market data and save it as a CSV.

Output:
    app/scripts/hyg_shy_raw.csv

The output contains the unadjusted daily closing prices:
    Date,HYG,SHY

This file is the raw input for:
    app/scripts/hyg_shy_proxy_analysis.py

No proxy calculation, scaling, or BAML reconstruction is performed here.
"""

import os

import pandas as pd
import yfinance as yf


START_DATE = "2017-08-17"
END_DATE = "2026-09-19"

OUTPUT_PATH = "app/scripts/hyg_shy_raw.csv"


print("Fetching raw HYG and SHY market data...")


# Download unadjusted daily closing prices.
hyg = yf.download(
    "HYG",
    start=START_DATE,
    end=END_DATE,
    auto_adjust=False,
    progress=False,
)["Close"]

shy = yf.download(
    "SHY",
    start=START_DATE,
    end=END_DATE,
    auto_adjust=False,
    progress=False,
)["Close"]


# Ensure each result is a 1D pandas Series.
if isinstance(hyg, pd.DataFrame):
    hyg = hyg.iloc[:, 0]

if isinstance(shy, pd.DataFrame):
    shy = shy.iloc[:, 0]


# Combine HYG and SHY by trading date.
raw_df = pd.DataFrame(
    {
        "HYG": hyg,
        "SHY": shy,
    }
).dropna()


# Convert the index into the required Date column.
raw_df.index.name = "Date"
raw_df = raw_df.reset_index()


# Keep the exact required column order.
raw_df = raw_df[
    [
        "Date",
        "HYG",
        "SHY",
    ]
]


# Ensure chronological ordering.
raw_df = raw_df.sort_values("Date").reset_index(drop=True)


# Save the raw dataset.
os.makedirs(
    os.path.dirname(OUTPUT_PATH),
    exist_ok=True,
)

raw_df.to_csv(
    OUTPUT_PATH,
    index=False,
)


print()
print("=== RAW HYG/SHY DATA ===")
print(f"Rows: {len(raw_df):,}")
print(
    f"Date range: "
    f"{raw_df['Date'].min().date()} → "
    f"{raw_df['Date'].max().date()}"
)
print(f"Missing HYG: {raw_df['HYG'].isna().sum():,}")
print(f"Missing SHY: {raw_df['SHY'].isna().sum():,}")
print(
    f"Duplicate dates: "
    f"{raw_df['Date'].duplicated().sum():,}"
)

print()
print(f"Saved raw dataset to: {OUTPUT_PATH}")
print()
print(raw_df.head(12).to_string(index=False))