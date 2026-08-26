"""Unit tests for APIKey model."""

import pytest
from datetime import datetime, timedelta, timezone

from app.models.api_key import APIKey


class TestAPIKeyModel:
    """Test APIKey model functionality."""

    def test_create_api_key(self):
        """Test creating an API key."""
        api_key = APIKey(
            user_id=1,
            name="Test API Key",
            key_prefix="abc123",
            hashed_key="hashed_key_here"
        )
        assert api_key.user_id == 1
        assert api_key.name == "Test API Key"
        assert api_key.key_prefix == "abc123"
        assert api_key.hashed_key == "hashed_key_here"
        assert api_key.is_active is True
        assert api_key.expires_at is None

    def test_api_key_defaults(self):
        """Test default values for APIKey."""
        api_key = APIKey(
            user_id=1,
            name="Test Key",
            key_prefix="abc123",
            hashed_key="hashed"
        )
        assert api_key.is_active is True
        assert api_key.permissions is None or api_key.permissions == []
        assert api_key.rate_limit_override is None

    def test_api_key_generation(self):
        """Test API key generation."""
        raw_key, hashed_key = APIKey.generate_key()
        assert len(raw_key) == 64  # 32 bytes hex = 64 chars
        assert len(hashed_key) == 64  # SHA-256 hex = 64 chars
        assert raw_key != hashed_key

    def test_api_key_hashing(self):
        """Test API key hashing."""
        raw_key = "test_key_123"
        hashed = APIKey.hash_key(raw_key)
        assert len(hashed) == 64
        assert hashed != raw_key
        # Same input should produce same hash
        assert APIKey.hash_key(raw_key) == hashed

    def test_api_key_prefix(self):
        """Test API key prefix extraction."""
        raw_key = "abcdefghijklmnopqrstuvwxyz1234567890"
        prefix = APIKey.get_prefix(raw_key)
        assert prefix == "abcdefgh"
        assert len(prefix) == 8

    def test_api_key_expiration(self):
        """Test API key expiration properties."""
        api_key = APIKey(
            user_id=1,
            name="Test Key",
            key_prefix="abc123",
            hashed_key="hashed"
        )
        assert api_key.is_expired is False
        assert api_key.is_valid is True

        # Set expiration in the past - use timezone-aware datetime
        api_key.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        assert api_key.is_expired is True
        assert api_key.is_valid is False

        # Set expiration in the future
        api_key.expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        assert api_key.is_expired is False
        assert api_key.is_valid is True

    def test_api_key_set_expiry(self):
        """Test setting API key expiration."""
        api_key = APIKey(
            user_id=1,
            name="Test Key",
            key_prefix="abc123",
            hashed_key="hashed"
        )
        api_key.set_expiry_days(30)
        assert api_key.expires_at is not None
        # Should be approximately 30 days from now
        diff = api_key.expires_at - datetime.now(timezone.utc)
        assert 29 <= diff.days <= 31

    def test_api_key_permissions(self):
        """Test API key permissions."""
        api_key = APIKey(
            user_id=1,
            name="Test Key",
            key_prefix="abc123",
            hashed_key="hashed",
            permissions=["read:btc", "read:predictions"]
        )
        assert api_key.permission_list == ["read:btc", "read:predictions"]
        assert api_key.has_permission("read:btc") is True
        assert api_key.has_permission("write:alerts") is False

    def test_api_key_update_last_used(self):
        """Test updating last_used timestamp."""
        api_key = APIKey(
            user_id=1,
            name="Test Key",
            key_prefix="abc123",
            hashed_key="hashed"
        )
        assert api_key.last_used_at is None
        api_key.update_last_used()
        assert api_key.last_used_at is not None

    def test_api_key_dict_excludes_hashed_key(self):
        """Test dict() method excludes hashed_key."""
        api_key = APIKey(
            user_id=1,
            name="Test Key",
            key_prefix="abc123",
            hashed_key="secret"
        )
        data = api_key.dict()
        assert "hashed_key" not in data
        assert data["name"] == "Test Key"
        assert data["key_prefix"] == "abc123"