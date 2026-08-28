#!/bin/bash
# cURL examples for exports endpoints

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
# 1. EXPORT PREDICTIONS AS CSV
# ============================================

echo "=== 1. Export Predictions as CSV ==="
curl -o predictions.csv \
  "$BASE_URL/export?export_type=predictions&format=csv&timeframe=24h" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
echo "✅ CSV saved to predictions.csv"
echo ""

# ============================================
# 2. EXPORT PREDICTIONS AS PNG
# ============================================

echo "=== 2. Export Predictions as PNG ==="
curl -o predictions.png \
  "$BASE_URL/export?export_type=predictions&format=png&timeframe=24h" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
echo "✅ PNG saved to predictions.png"
echo ""

# ============================================
# 3. EXPORT PREDICTIONS AS PDF
# ============================================

echo "=== 3. Export Predictions as PDF ==="
curl -o predictions.pdf \
  "$BASE_URL/export?export_type=predictions&format=pdf&timeframe=24h" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
echo "✅ PDF saved to predictions.pdf"
echo ""

# ============================================
# 4. GET EXPORT HISTORY
# ============================================

echo "=== 4. Get Export History ==="
curl -X GET "$BASE_URL/export/history" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq

echo ""

# ============================================
# 5. DOWNLOAD PREVIOUS EXPORT
# ============================================

echo "=== 5. Download Previous Export ==="
# Replace 1 with the actual export ID from history
EXPORT_ID=1
curl -o export_$EXPORT_ID.csv \
  "$BASE_URL/export/$EXPORT_ID/download" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
echo "✅ Export $EXPORT_ID downloaded"