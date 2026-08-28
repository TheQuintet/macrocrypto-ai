#!/bin/bash
# cURL examples for authentication endpoints

BASE_URL="http://localhost:8000/api/v1"

# ============================================
# 1. REGISTER A NEW USER
# ============================================

echo "=== 1. Register User ==="
curl -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }' | jq

echo ""

# ============================================
# 2. LOGIN
# ============================================

echo "=== 2. Login ==="
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "SecurePass123!"
  }')

echo "$LOGIN_RESPONSE" | jq

# Extract tokens
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.refresh_token')
echo "Access Token: ${ACCESS_TOKEN:0:50}..."
echo "Refresh Token: ${REFRESH_TOKEN:0:50}..."
echo ""

# ============================================
# 3. GET CURRENT USER
# ============================================

echo "=== 3. Get Current User ==="
curl -X GET "$BASE_URL/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq

echo ""

# ============================================
# 4. REFRESH TOKEN
# ============================================

echo "=== 4. Refresh Token ==="
curl -X POST "$BASE_URL/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"$REFRESH_TOKEN\"
  }" | jq

echo ""

# ============================================
# 5. CHANGE PASSWORD
# ============================================

echo "=== 5. Change Password ==="
curl -X POST "$BASE_URL/auth/change-password" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "SecurePass123!",
    "new_password": "NewSecurePass456!"
  }' | jq

echo ""

# ============================================
# 6. LOGOUT
# ============================================

echo "=== 6. Logout ==="
curl -X POST "$BASE_URL/auth/logout" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq