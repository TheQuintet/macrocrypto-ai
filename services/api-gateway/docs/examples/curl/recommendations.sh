#!/bin/bash
# cURL examples for recommendations endpoints

BASE_URL="http://localhost:8000/api/v1"

# First, get a token
echo "=== Getting token ==="
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "SecurePass123!"
  }')
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
echo "Token obtained"
echo ""

# ============================================
# 1. GET TRADE RECOMMENDATIONS
# ============================================

echo "=== 1. Get Trade Recommendations (24h, moderate) ==="
curl -X GET "$BASE_URL/recommendations/btc?timeframe=24h&risk_level=moderate" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.recommendation'

echo ""

# ============================================
# 2. GET RECOMMENDATIONS (7d, high risk)
# ============================================

echo "=== 2. Get Trade Recommendations (7d, high risk) ==="
curl -X GET "$BASE_URL/recommendations/btc?timeframe=7d&risk_level=high" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.recommendation.recommendation, .recommendation.risk_reward_ratio'

echo ""

# ============================================
# 3. GET RECOMMENDATIONS (low risk)
# ============================================

echo "=== 3. Get Trade Recommendations (24h, low risk) ==="
curl -X GET "$BASE_URL/recommendations/btc?timeframe=24h&risk_level=low" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.recommendation.stop_loss, .recommendation.take_profit'