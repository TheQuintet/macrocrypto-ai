#!/bin/bash
# cURL examples for market data endpoints

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
# 1. GET BTC PRICES
# ============================================

echo "=== 1. Get BTC Prices ==="
curl -X GET "$BASE_URL/btc/prices?limit=5&offset=0" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.symbol, .total, (.prices | length)'

echo ""

# ============================================
# 2. GET PRICES WITH DATE RANGE
# ============================================

echo "=== 2. Get Prices with Date Range ==="
curl -X GET "$BASE_URL/btc/prices?start_date=2026-08-01&end_date=2026-08-28" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.total'

echo ""

# ============================================
# 3. GET MACRO INDICATORS
# ============================================

echo "=== 3. Get Macro Indicators ==="
curl -X GET "$BASE_URL/indicators" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.indicators | keys'

echo ""

# ============================================
# 4. GET CORRELATION ANALYSIS
# ============================================

echo "=== 4. Get Correlation Analysis ==="
curl -X GET "$BASE_URL/correlation/btc?window=30d" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.correlations'

echo ""

# ============================================
# 5. GET REGIME DATA
# ============================================

echo "=== 5. Get Regime Data ==="
curl -X GET "$BASE_URL/regimes/btc?timeframe=1w" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.current_regime.regime_type, .current_regime.avg_return'