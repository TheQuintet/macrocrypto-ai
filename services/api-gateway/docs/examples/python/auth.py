"""Python examples for authentication endpoints."""

import requests
import json

# ============================================
# BASE URL
# ============================================

BASE_URL = "http://localhost:8000/api/v1"


# ============================================
# 1. REGISTER A NEW USER
# ============================================

def register_user():
    """Register a new user."""
    url = f"{BASE_URL}/auth/register"
    payload = {
        "email": "user@example.com",
        "username": "johndoe",
        "password": "SecurePass123!",
        "full_name": "John Doe"
    }
    response = requests.post(url, json=payload)
    print(f"Register Status: {response.status_code}")
    print(f"Register Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

# Output:
# {
#   "id": 1,
#   "email": "user@example.com",
#   "username": "johndoe",
#   "full_name": "John Doe",
#   "role": "user",
#   "status": "pending",
#   "is_email_verified": false,
#   "created_at": "2026-08-28T..."
# }


# ============================================
# 2. LOGIN
# ============================================

def login():
    """Login and get tokens."""
    url = f"{BASE_URL}/auth/login"
    payload = {
        "username": "johndoe",
        "password": "SecurePass123!"
    }
    response = requests.post(url, json=payload)
    print(f"Login Status: {response.status_code}")
    data = response.json()
    print(f"Access Token: {data.get('access_token', 'N/A')[:50]}...")
    print(f"Refresh Token: {data.get('refresh_token', 'N/A')[:50]}...")
    return data

# Output:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIs...",
#   "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
#   "token_type": "bearer"
# }


# ============================================
# 3. GET CURRENT USER
# ============================================

def get_current_user(access_token):
    """Get current user profile."""
    url = f"{BASE_URL}/auth/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    print(f"Get User Status: {response.status_code}")
    print(f"User: {json.dumps(response.json(), indent=2)}")
    return response.json()

# Output:
# {
#   "id": 1,
#   "email": "user@example.com",
#   "username": "johndoe",
#   "full_name": "John Doe",
#   "role": "user",
#   "status": "active",
#   "is_email_verified": true,
#   "created_at": "2026-08-28T..."
# }


# ============================================
# 4. REFRESH TOKEN
# ============================================

def refresh_token(refresh_token):
    """Refresh access token."""
    url = f"{BASE_URL}/auth/refresh"
    payload = {"refresh_token": refresh_token}
    response = requests.post(url, json=payload)
    print(f"Refresh Status: {response.status_code}")
    data = response.json()
    print(f"New Access Token: {data.get('access_token', 'N/A')[:50]}...")
    return data

# Output:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIs...",
#   "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
#   "token_type": "bearer"
# }


# ============================================
# 5. CHANGE PASSWORD
# ============================================

def change_password(access_token, current_password, new_password):
    """Change user password."""
    url = f"{BASE_URL}/auth/change-password"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "current_password": current_password,
        "new_password": new_password
    }
    response = requests.post(url, json=payload, headers=headers)
    print(f"Change Password Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()


# ============================================
# 6. LOGOUT
# ============================================

def logout(access_token):
    """Logout (client-side token discard)."""
    url = f"{BASE_URL}/auth/logout"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(url, headers=headers)
    print(f"Logout Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()