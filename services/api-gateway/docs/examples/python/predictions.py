"""Python examples for predictions endpoints."""

import requests
import json

# ============================================
# BASE URL
# ============================================

BASE_URL = "http://localhost:8000/api/v1"


# ============================================
# 1. GET BTC PREDICTIONS (24h)
# ============================================

def get_predictions_24h(access_token):
    """Get 24-hour BTC predictions."""
    url = f"{BASE_URL}/predict/btc"
    params = {
        "horizon": "24h",
        "model_type": "ensemble"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, params=params, headers=headers)
    print(f"Predictions Status: {response.status_code}")
    data = response.json()
    print(f"Symbol: {data.get('symbol')}")
    print(f"Timeframe: {data.get('timeframe')}")
    print(f"Current Price: ${data.get('current_price', 0):,.2f}")
    print(f"Trend: {data.get('trend_direction')}")
    print(f"Predictions: {len(data.get('predictions', []))}")
    return data

# Output:
# {
#   "symbol": "BTC",
#   "timeframe": "24h",
#   "model_type": "ensemble",
#   "current_price": 45000.00,
#   "change_percent": 2.5,
#   "trend_direction": "up",
#   "predictions": [...],
#   "timestamp": "...",
#   "cached": false
# }


# ============================================
# 2. GET BTC PREDICTIONS (7d)
# ============================================

def get_predictions_7d(access_token):
    """Get 7-day BTC predictions."""
    url = f"{BASE_URL}/predict/btc"
    params = {
        "horizon": "7d",
        "model_type": "ensemble"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, params=params, headers=headers)
    print(f"Predictions Status: {response.status_code}")
    data = response.json()
    print(f"Symbol: {data.get('symbol')}")
    print(f"Timeframe: {data.get('timeframe')}")
    print(f"Predictions: {len(data.get('predictions', []))}")
    return data


# ============================================
# 3. GET PREDICTION ACCURACY
# ============================================

def get_accuracy(access_token):
    """Get prediction accuracy metrics."""
    url = f"{BASE_URL}/predict/btc/accuracy"
    params = {"days": 30}
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, params=params, headers=headers)
    print(f"Accuracy Status: {response.status_code}")
    data = response.json()
    print(f"Overall Accuracy: {data.get('overall_accuracy', 0):.1f}%")
    print(f"RMSE: {data.get('rmse', 0):.2f}")
    print(f"MAE: {data.get('mae', 0):.2f}")
    print(f"Predictions Count: {data.get('predictions_count', 0)}")
    return data

# Output:
# {
#   "symbol": "BTC",
#   "days": 30,
#   "overall_accuracy": 85.5,
#   "rmse": 125.30,
#   "mae": 98.75,
#   "mape": 2.1,
#   "predictions_count": 720,
#   "market_condition_breakdown": {...},
#   "threshold_warning": false
# }