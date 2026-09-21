"""
Create and inspect the HYG/SHY credit-stress proxy.

Input:
    app/scripts/hyg_shy_raw.csv

Output:
    app/scripts/high_yield_credit_stress_proxy.csv

The proxy is:
    (HYG / SHY).pct_change()

This is a derived market feature.
It is NOT BAMLH0A0HYM2 and is NOT a reconstructed credit spread.
"""

import os

import pandas as pd


INPUT_PATH = "app/scripts/hyg_shy_raw.csv"
OUTPUT_PATH = "app/scripts/high_yield_credit_stress_proxy.csv"


print("Loading raw HYG/SHY data...")

df = pd.read_csv(INPUT_PATH, parse_dates=["Date"])

df = df.sort_values("Date").reset_index(drop=True)


# ---------------------------------------------------------
# 1. Validate raw inputs
# ---------------------------------------------------------

print()
print("=== RAW INPUT ===")
print(f"Rows: {len(df):,}")
print(f"Date range: {df['Date'].min().date()} → {df['Date'].max().date()}")
print(f"Duplicate dates: {df['Date'].duplicated().sum():,}")
print(f"Missing HYG: {df['HYG'].isna().sum():,}")
print(f"Missing SHY: {df['SHY'].isna().sum():,}")


# ---------------------------------------------------------
# 2. Calculate HYG / SHY
# ---------------------------------------------------------

df["hyg_shy_ratio"] = df["HYG"] / df["SHY"]


# ---------------------------------------------------------
# 3. Calculate the recommended proxy
# ---------------------------------------------------------

df["high_yield_credit_stress_proxy"] = (
    df["hyg_shy_ratio"].pct_change()
)


# ---------------------------------------------------------
# 4. Keep only the feature we intend to evaluate
# ---------------------------------------------------------

proxy_df = df[
    [
        "Date",
        "high_yield_credit_stress_proxy",
    ]
].copy()


# ---------------------------------------------------------
# 5. Basic validation
# ---------------------------------------------------------

print()
print("=== PROXY ===")
print(
    f"Rows: {len(proxy_df):,}"
)

print(
    f"Date range: "
    f"{proxy_df['Date'].min().date()} → "
    f"{proxy_df['Date'].max().date()}"
)

print(
    f"Missing proxy values: "
    f"{proxy_df['high_yield_credit_stress_proxy'].isna().sum():,}"
)

print(
    f"Duplicate dates: "
    f"{proxy_df['Date'].duplicated().sum():,}"
)


# ---------------------------------------------------------
# 6. Proxy statistics
# ---------------------------------------------------------

print()
print("=== PROXY STATISTICS ===")
print(
    proxy_df["high_yield_credit_stress_proxy"]
    .describe()
    .to_string()
)


# ---------------------------------------------------------
# 7. Inspect largest movements
# ---------------------------------------------------------

print()
print("=== LARGEST NEGATIVE MOVEMENTS ===")

print(
    proxy_df.nsmallest(
        10,
        "high_yield_credit_stress_proxy",
    ).to_string(index=False)
)


print()
print("=== LARGEST POSITIVE MOVEMENTS ===")

print(
    proxy_df.nlargest(
        10,
        "high_yield_credit_stress_proxy",
    ).to_string(index=False)
)


# ---------------------------------------------------------
# 8. Inspect selected historical dates
# ---------------------------------------------------------

checkpoint_dates = [
    "2017-08-17",
    "2020-03-09",
    "2020-03-16",
    "2020-03-23",
    "2021-03-19",
    "2021-03-22",
    "2022-06-13",
    "2023-09-18",
    "2025-04-09",
    "2026-09-18",
]

checkpoints = proxy_df[
    proxy_df["Date"].dt.strftime("%Y-%m-%d").isin(checkpoint_dates)
]

print()
print("=== SELECTED DATES ===")
print(checkpoints.to_string(index=False))


# ---------------------------------------------------------
# 9. Save candidate proxy
# ---------------------------------------------------------

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

proxy_df.to_csv(
    OUTPUT_PATH,
    index=False,
)

print()
print("=== COMPLETE ===")
print(f"Saved candidate proxy to: {OUTPUT_PATH}")
print()
print("The proxy is a derived HYG/SHY market signal.")
print("It is NOT BAMLH0A0HYM2.")
print("No database or ML dataset was modified.")