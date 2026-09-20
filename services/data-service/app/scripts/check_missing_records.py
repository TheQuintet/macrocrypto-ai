import pandas as pd

# Load dataset
df = pd.read_csv("app/data/ml_btc_daily_raw.csv")
date_col = "observation_date"

if date_col in df.columns:
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(by=date_col).reset_index(drop=True)

total_rows = len(df)


# # ==========================================
start_date = pd.to_datetime("2017-08-17 00:00:00+00:00")

if df[date_col].dt.tz is not None and start_date.tz is not None:
    pass
elif df[date_col].dt.tz is not None:
    start_date = start_date.tz_localize(df[date_col].dt.tz)
elif start_date.tz is not None:
    df[date_col] = df[date_col].dt.tz_localize("UTC")
    start_date = start_date.tz_convert("UTC")
    
end_date = df[date_col].max()
naive_start = start_date.tz_localize(None) if start_date.tz else start_date
naive_end = end_date.tz_localize(None) if end_date.tz else end_date

total_calendar_days = (naive_end - naive_start).days + 1
trading_days = len(pd.bdate_range(start=naive_start, end=naive_end))
total_months = (naive_end.year - naive_start.year) * 12 + (naive_end.month - naive_start.month) + 1
total_quarters = int(total_months / 3.0)

frequency_map = {
    "btc_price": ("Daily (24/7)", total_calendar_days),
    "btc_volume": ("Daily (24/7)", total_calendar_days),
    "active_addresses": ("Daily (24/7)", total_calendar_days),
    "btc_dominance": ("Daily (24/7)", total_calendar_days),
    "dxy": ("Daily (Trading Days)", trading_days),
    "ten_year_treasury": ("Daily (Trading Days)", trading_days),
    "nasdaq_composite": ("Daily (Trading Days)", trading_days),
    "equity_corr": ("Daily (Trading Days)", trading_days),
    "vix": ("Daily (Trading Days)", trading_days),
    "high_yield_spread": ("Daily (Trading Days)", trading_days),
    "cpi": ("Monthly", total_months),
    "federal_funds_rate": ("Monthly (FRED)", total_months),
    "m2_money_supply": ("Monthly", total_months),
    "unemployment": ("Monthly", total_months),
    "gdp": ("Quarterly", total_quarters),
}

print(f"\nPART 3: DETAILED GAP INTERVALS BY FEATURE (FREQUENCY-FILTERED)")
print("-" * 88)
print(f"{'Feature':<21} | {'Gap Start':<10} | {'Gap End':<10} | {'Gap Length':>10} | {'Finding':<30}")
print("-" * 88)

has_gaps = False
for column in df.columns:
    if column.endswith("_timestamp") or column == date_col:
        continue
    
    freq, _ = frequency_map.get(column, ("Daily", 0))
    if column == "gold_spot":
        freq = "Daily (Trading Days)"
        
    if "Monthly" in freq:
        min_length = 60
    elif "Quarterly" in freq:
        min_length = 120
    else:
        # Threshold of 4 days for daily/trading-day features to account for weekends/holidays
        min_length = 4
    
    valid_rows = df.dropna(subset=[column])
    if valid_rows.empty:
        continue
    
    min_date = valid_rows[date_col].min()
    max_date = valid_rows[date_col].max()
    
    active_range = df[(df[date_col] >= min_date) & (df[date_col] <= max_date)].copy()
    active_range['is_missing'] = active_range[column].isna()
    active_range['block'] = (active_range['is_missing'] != active_range['is_missing'].shift()).cumsum()
    
    for _, group in active_range[active_range['is_missing']].groupby('block'):
        length = len(group)
        if length >= min_length:
            start_d = group[date_col].min()
            end_d = group[date_col].max()
            
            start_str = start_d.strftime('%Y-%m-%d')
            end_str = end_d.strftime('%Y-%m-%d')
            length_str = f"{length} days"
            
            finding = "Historical source coverage gap" if length > 100 else "Upstream source coverage gap"
            
            print(f"{column:<21} | {start_str:<10} | {end_str:<10} | {length_str:>10} | {finding:<30}")
            has_gaps = True

if not has_gaps:
    print(f"{'No gaps meeting frequency thresholds found across active ranges.':<88}")

print("-" * 88)