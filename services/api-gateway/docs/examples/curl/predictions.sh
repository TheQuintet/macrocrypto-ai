#!/bin/bash
# cURL examples for predictions endpoints

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
# 1. GET BTC PREDICTIONS (24h)
# ============================================

echo "=== 1. Get BTC Predictions (24h) ==="
curl -X GET "$BASE_URL/predict/btc?horizon=24h&model_type=ensemble" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.current_price, .trend_direction, (.predictions | length)'

echo ""

# ============================================
# 2. GET BTC PREDICTIONS (7d)
# ============================================

echo "=== 2. Get BTC Predictions (7d) ==="
curl -X GET "$BASE_URL/predict/btc?horizon=7d&model_type=ensemble" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.timeframe, (.predictions | length)'

echo ""

# ============================================
# 3. GET PREDICTION ACCURACY
# ============================================

echo "=== 3. Get Prediction Accuracy ==="
curl -X GET "$BASE_URL/predict/btc/accuracy?days=30" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.overall_accuracy, .rmse, .mae'

echo ""