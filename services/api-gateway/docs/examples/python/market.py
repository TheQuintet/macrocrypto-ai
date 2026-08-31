"""Python examples for market data endpoints."""

import requests
import json

# ============================================
# BASE URL
# ============================================

BASE_URL = "http://localhost:8000/api/v1"


# ============================================
# 1. GET BTC PRICES (with pagination)
# ============================================

def get_prices(access_token):
    """Get historical BTC prices with pagination."""
    url = f"{BASE_URL}/btc/prices"
    params = {
        "limit": 10,
        "offset": 0
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, params=params, headers=headers)
    print(f"Prices Status: {response.status_code}")
    data = response.json()
    print(f"Symbol: {data.get('symbol')}")
    print(f"Total Records: {data.get('total')}")
    print(f"Records Returned: {len(data.get('prices', []))}")
    return data

# Output:
# {
#   "symbol": "BTC",
#   "prices": [...],
#   "total": 100,
#   "limit": 10,
#   "offset": 0,
#   "timestamp": "...",
#   "cached": false
# }


# ============================================
# 2. GET PRICES WITH DATE RANGE
# ============================================

def get_prices_date_range(access_token):
    """Get BTC prices with date range filtering."""
    url = f"{BASE_URL}/btc/prices"
    params = {
        "start_date": "2026-08-01",
        "end_date": "2026-08-28",
        "limit": 100
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, params=params, headers=headers)
    print(f"Prices Status: {response.status_code}")
    print(f"Total Records: {response.json().get('total', 0)}")
    return response.json()


# ============================================
# 3. GET MACRO INDICATORS
# ============================================

def get_indicators(access_token):
    """Get macroeconomic indicators."""
    url = f"{BASE_URL}/indicators"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    print(f"Indicators Status: {response.status_code}")
    data = response.json()
    for name, indicator in data.get("indicators", {}).items():
        print(f"{name}: {indicator.get('value')} {indicator.get('unit')}")
    return data

# Output:
# {
#   "indicators": {
#     "GDP": {"value": 28.78, "previous": 28.52, ...},
#     "Inflation": {"value": 3.2, "previous": 3.5, ...},
#     "Interest Rates": {"value": 5.50, "previous": 5.50, ...}
#   }
# }


# ============================================
# 4. GET CORRELATION ANALYSIS
# ============================================

def get_correlation(access_token):
    """Get BTC-macro correlation analysis."""
    url = f"{BASE_URL}/correlation/btc"
    params = {"window": "30d"}
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, params=params, headers=headers)
    print(f"Correlation Status: {response.status_code}")
    data = response.json()
    for indicator, corr in data.get("correlations", {}).items():
        print(f"{indicator}: {corr.get('value'):+.2f} ({corr.get('strength')})")
    return data

# Output:
# {
#   "symbol": "BTC",
#   "window": "30d",
#   "correlations": {
#     "S&P 500": {"value": 0.65, "strength": "moderate"},
#     "DXY": {"value": -0.45, "strength": "moderate"},
#     "Gold": {"value": 0.35, "strength": "weak"}
#   }
# }


# ============================================
# 5. GET REGIME DATA
# ============================================

def get_regimes(access_token):
    """Get market regime data."""
    url = f"{BASE_URL}/regimes/btc"
    params = {"timeframe": "1w"}
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, params=params, headers=headers)
    print(f"Regimes Status: {response.status_code}")
    data = response.json()
    current = data.get("current_regime", {})
    print(f"Current Regime: {current.get('regime_type')}")
    print(f"Duration: {current.get('duration_days', 0)} days")
    print(f"Avg Return: {current.get('avg_return', 0):.2f}%")
    return data

# Output:
# {
#   "symbol": "BTC",
#   "timeframe": "1w",
#   "regimes": [...],
#   "current_regime": {
#     "regime_type": "bull",
#     "start_date": "...",
#     "duration_days": 30,
#     "avg_return": 12.5
#   }
# }