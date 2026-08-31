"""Unit tests for security utilities (password hashing, JWT)."""

import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)
from app.core.config import settings


class TestPasswordHashing:
    """Test password hashing utilities."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPass123"
        hashed = get_password_hash(password)
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 10

    def test_verify_password(self):
        """Test password verification."""
        password = "TestPass123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPass", hashed) is False

    def test_hash_different_passwords(self):
        """Test that different passwords produce different hashes."""
        hash1 = get_password_hash("Password1")
        hash2 = get_password_hash("Password2")
        assert hash1 != hash2


class TestJWT:
    """Test JWT token utilities."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": 1, "username": "testuser"}
        token = create_access_token(data)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20

        # Decode and verify
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert decoded["sub"] == "1"
        assert decoded["username"] == "testuser"
        assert decoded["type"] == "access"
        assert "exp" in decoded
        assert "iat" in decoded

    def test_create_access_token_with_expiry(self):
        """Test access token with custom expiry."""
        data = {"sub": 1}
        expires_delta = timedelta(minutes=5)
        token = create_access_token(data, expires_delta)
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        exp = datetime.fromtimestamp(decoded["exp"], timezone.utc)
        now = datetime.now(timezone.utc)
        # Should expire in about 5 minutes
        assert (exp - now).total_seconds() >= 280  # ~4.6 minutes

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": 1, "username": "testuser"}
        token = create_refresh_token(data)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20

        # Decode and verify
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert decoded["sub"] == "1"
        assert decoded["username"] == "testuser"
        assert decoded["type"] == "refresh"
        assert "exp" in decoded
        assert "iat" in decoded

    def test_decode_token(self):
        """Test token decoding."""
        data = {"sub": 1, "username": "testuser"}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert decoded["sub"] == 1  # Should convert to int
        assert decoded["username"] == "testuser"
        assert decoded["type"] == "access"

    def test_decode_invalid_token(self):
        """Test decoding an invalid token raises exception."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid_token")
        assert exc_info.value.status_code == 401

    def test_verify_token_type(self):
        """Test token type verification."""
        data = {"sub": 1}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        access_decoded = decode_token(access_token)
        refresh_decoded = decode_token(refresh_token)

        assert verify_token_type(access_decoded, "access") is True
        assert verify_token_type(refresh_decoded, "refresh") is True

        # Wrong type should raise exception
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            verify_token_type(access_decoded, "refresh")