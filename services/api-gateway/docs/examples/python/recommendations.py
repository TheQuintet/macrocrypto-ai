"""Python examples for recommendations endpoints."""

import requests
import json

# ============================================
# BASE URL
# ============================================

BASE_URL = "http://localhost:8000/api/v1"


# ============================================
# 1. GET TRADE RECOMMENDATIONS
# ============================================

def get_recommendations(access_token):
    """Get trade recommendations for BTC."""
    url = f"{BASE_URL}/recommendations/btc"
    params = {
        "timeframe": "24h",
        "risk_level": "moderate"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, params=params, headers=headers)
    print(f"Recommendations Status: {response.status_code}")
    data = response.json()
    rec = data.get("recommendation", {})
    print(f"Recommendation: {rec.get('recommendation')}")
    print(f"Confidence: {rec.get('confidence', 0):.0%}")
    print(f"Entry Price: ${rec.get('entry_price', 0):,.2f}")
    print(f"Stop Loss: ${rec.get('stop_loss', 0):,.2f}")
    print(f"Take Profit: ${rec.get('take_profit', 0):,.2f}")
    print(f"Risk/Reward: {rec.get('risk_reward_ratio', 0):.1f}")
    print(f"Explanation: {rec.get('explanation', '')[:100]}...")
    return data

# Output:
# {
#   "symbol": "BTC",
#   "timeframe": "24h",
#   "risk_level": "moderate",
#   "recommendation": {
#     "recommendation": "BUY",
#     "confidence": 0.85,
#     "entry_price": 45000.00,
#     "stop_loss": 43650.00,
#     "take_profit": 47700.00,
#     "risk_level": "moderate",
#     "risk_reward_ratio": 2.0,
#     "time_horizon": "24h",
#     "explanation": "Based on 24h predictions showing up trend...",
#     "historical_accuracy": 0.88
#   }
# }


# ============================================
# 2. GET RECOMMENDATIONS (7d, high risk)
# ============================================

def get_recommendations_high_risk(access_token):
    """Get 7-day high-risk trade recommendations."""
    url = f"{BASE_URL}/recommendations/btc"
    params = {
        "timeframe": "7d",
        "risk_level": "high"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, params=params, headers=headers)
    print(f"Recommendations Status: {response.status_code}")
    data = response.json()
    rec = data.get("recommendation", {})
    print(f"Recommendation: {rec.get('recommendation')}")
    print(f"Risk/Reward: {rec.get('risk_reward_ratio', 0):.1f}")
    return data


# ============================================
# 3. GET RECOMMENDATIONS (low risk)
# ============================================

def get_recommendations_low_risk(access_token):
    """Get low-risk trade recommendations."""
    url = f"{BASE_URL}/recommendations/btc"
    params = {
        "timeframe": "24h",
        "risk_level": "low"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, params=params, headers=headers)
    print(f"Recommendations Status: {response.status_code}")
    data = response.json()
    rec = data.get("recommendation", {})
    print(f"Recommendation: {rec.get('recommendation')}")
    print(f"Stop Loss: ${rec.get('stop_loss', 0):,.2f}")
    print(f"Take Profit: ${rec.get('take_profit', 0):,.2f}")
    return data