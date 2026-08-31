#!/bin/bash
# cURL examples for WebSocket endpoints

BASE_URL="http://localhost:8000"

# ============================================
# 1. WEBSOCKET STATUS
# ============================================

echo "=== 1. WebSocket Status ==="
curl -X GET "$BASE_URL/ws/status" | jq

echo ""

# ============================================
# 2. WEBSOCKET CONNECTION (with wscat)
# ============================================

echo "=== 2. WebSocket Connection (wscat) ==="
echo "Run: wscat -c \"$BASE_URL/ws\""
echo ""

# ============================================
# 3. WEBSOCKET WITH AUTHENTICATION
# ============================================

echo "=== 3. WebSocket with Authentication ==="
# First, get a token
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "SecurePass123!"
  }')
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
echo "Run: wscat -c \"$BASE_URL/ws?token=$ACCESS_TOKEN\""