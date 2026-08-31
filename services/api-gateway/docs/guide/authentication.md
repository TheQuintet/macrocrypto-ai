```markdown
# Authentication Guide

This guide explains how authentication works in the MacroCrypto AI API.

## Overview

The API uses JWT (JSON Web Tokens) for authentication. The flow is:

1. User registers with email, username, and password
2. User logs in to receive access and refresh tokens
3. User includes the access token in all API requests
4. When the access token expires, user uses the refresh token to get a new one

## Token Lifecycle

### Access Token
- **Purpose**: Authorize API requests
- **Expiry**: 15 minutes
- **Format**: JWT (Bearer token)
- **Usage**: Include in `Authorization` header

### Refresh Token
- **Purpose**: Obtain new access tokens
- **Expiry**: 7 days
- **Format**: JWT
- **Usage**: Send to `/auth/refresh` endpoint

## Endpoints

### Register

**Endpoint:** `POST /api/v1/auth/register`

**Request:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "role": "user",
  "status": "pending",
  "is_email_verified": false,
  "created_at": "2026-08-28T..."
}
```

**Error Responses:**
| Code | Description |
|------|-------------|
| 400 | Email already registered, username taken, or invalid input |
| 422 | Validation error (e.g., weak password) |

### Login

**Endpoint:** `POST /api/v1/auth/login`

**Request:**
```json
{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Error Responses:**
| Code | Description |
|------|-------------|
| 401 | Invalid username or password |
| 403 | Account is pending, inactive, or suspended |

### Refresh Token

**Endpoint:** `POST /api/v1/auth/refresh`

**Request:**
```json
{
  "refresh_token": "YOUR_REFRESH_TOKEN"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Error Responses:**
| Code | Description |
|------|-------------|
| 401 | Invalid or expired refresh token |

### Get Current User

**Endpoint:** `GET /api/v1/auth/me`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "role": "user",
  "status": "active",
  "is_email_verified": true,
  "created_at": "2026-08-28T..."
}
```

### Change Password

**Endpoint:** `POST /api/v1/auth/change-password`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Request:**
```json
{
  "current_password": "SecurePass123!",
  "new_password": "NewSecurePass456!"
}
```

### Logout

**Endpoint:** `POST /api/v1/auth/logout`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Note:** Since JWT tokens are stateless, logout only notifies the client to discard tokens.

## Python Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Register
def register_user():
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": "user@example.com",
        "username": "johndoe",
        "password": "SecurePass123!",
        "full_name": "John Doe"
    })
    return response.json()

# Login
def login():
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "johndoe",
        "password": "SecurePass123!"
    })
    return response.json()

# Get current user
def get_current_user(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    return response.json()

# Refresh token
def refresh_token(refresh_token):
    response = requests.post(f"{BASE_URL}/auth/refresh", json={
        "refresh_token": refresh_token
    })
    return response.json()

# Usage
user = register_user()
tokens = login()
user_info = get_current_user(tokens["access_token"])
new_tokens = refresh_token(tokens["refresh_token"])
```

## cURL Examples

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "SecurePass123!"
  }'

# Get current user
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Refresh token
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'

# Change password
curl -X POST http://localhost:8000/api/v1/auth/change-password \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "SecurePass123!",
    "new_password": "NewSecurePass456!"
  }'

# Logout
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Security Best Practices

1. **Store tokens securely**: Never store tokens in plain text or localStorage
2. **Use HTTPS in production**: Always use HTTPS for API calls
3. **Refresh token rotation**: Get a new refresh token when refreshing
4. **Short-lived access tokens**: Access tokens expire in 15 minutes
5. **Secure password storage**: Passwords are hashed using bcrypt
6. **Rate limiting**: Protects against brute force attacks
7. **Token validation**: All tokens are validated on every request
8. **CORS configuration**: Only allow trusted origins

## Error Handling

| Code | Description | Solution |
|------|-------------|----------|
| 401 | Unauthorized | Check token is valid and not expired |
| 403 | Forbidden | Check user has required permissions |
| 422 | Validation error | Fix request validation errors |

## Common Issues

### Token Expired

If you receive a 401 error, your access token may have expired:

```python
def make_authenticated_request(url, access_token, refresh_token):
    response = requests.get(url, headers={"Authorization": f"Bearer {access_token}"})
    
    if response.status_code == 401:
        # Refresh token
        refresh_response = requests.post(f"{BASE_URL}/auth/refresh", json={
            "refresh_token": refresh_token
        })
        new_tokens = refresh_response.json()
        access_token = new_tokens["access_token"]
        
        # Retry with new token
        response = requests.get(url, headers={"Authorization": f"Bearer {access_token}"})
    
    return response
```

### Account Not Verified

If your account is pending verification:

```json
{
  "detail": "Account is pending verification. Please verify your email."
}
```

Solution: Check your email for verification link.

### Invalid Credentials

```json
{
  "detail": "Incorrect username or password"
}
```

Solution: Verify your username and password are correct.
```