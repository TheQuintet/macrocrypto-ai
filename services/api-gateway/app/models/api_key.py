"""API Key model for external API access.

This module defines the APIKey model for managing API keys
that allow external applications to access the API.
"""

from datetime import datetime, timedelta
from typing import Optional, List
import secrets
import json

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base


class APIKey(Base):
    """API Key model for external API access.

    Attributes:
        user_id: Foreign key to the owning user
        name: Human-readable name for the API key
        key_prefix: First few characters of the key for display
        hashed_key: SHA-256 hashed API key (full key stored by client)
        permissions: JSON array of permissions (e.g., ["read:btc", "write:alerts"])
        is_active: Whether the key is currently active
        expires_at: Optional expiration timestamp
        last_used_at: Timestamp when the key was last used
        rate_limit_override: Optional custom rate limit for this key
        extra_data: Additional metadata as JSON
        user: Relationship to the owning User
    """

    __tablename__ = "api_keys"

    # Foreign key to user
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the owning user",
    )

    # Key identification
    name = Column(
        String(100),
        nullable=False,
        doc="Human-readable name for the API key",
    )
    key_prefix = Column(
        String(8),
        nullable=False,
        doc="First 8 characters of the key for display",
    )
    hashed_key = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        doc="SHA-256 hashed API key",
    )

    # Permissions and access control
    permissions = Column(
        JSON,
        nullable=True,
        default=list,
        doc="JSON array of permissions (e.g., ['read:btc', 'write:alerts'])",
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the key is currently active",
    )

    # Expiration and usage
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Optional expiration timestamp",
    )
    last_used_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when the key was last used",
    )
    rate_limit_override = Column(
        Integer,
        nullable=True,
        doc="Optional custom rate limit (requests per minute) for this key",
    )

    # Additional data - renamed from 'metadata' to avoid SQLAlchemy reserved name
    extra_data = Column(
        JSON,
        nullable=True,
        default=dict,
        doc="Additional metadata as JSON",
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="api_keys",
        doc="The user who owns this API key",
    )

    def __repr__(self) -> str:
        """String representation of the API key."""
        return f"<APIKey(id={self.id}, name='{self.name}', prefix='{self.key_prefix}')>"

    @staticmethod
    def generate_key() -> tuple[str, str]:
        """Generate a new API key and its hash.

        Returns:
            tuple: (full_key, hashed_key) where full_key is the raw key
                   to give to the user and hashed_key is for storage.
        """
        # Generate a secure random key (32 bytes = 256 bits)
        raw_key = secrets.token_hex(32)
        # Return full key and its SHA-256 hash
        return raw_key, APIKey.hash_key(raw_key)

    @staticmethod
    def hash_key(raw_key: str) -> str:
        """Hash an API key using SHA-256.

        Args:
            raw_key: The raw API key to hash.

        Returns:
            str: The SHA-256 hashed key.
        """
        import hashlib
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @staticmethod
    def get_prefix(raw_key: str) -> str:
        """Get the prefix of an API key for display.

        Args:
            raw_key: The raw API key.

        Returns:
            str: First 8 characters of the key.
        """
        return raw_key[:8]

    @property
    def is_expired(self) -> bool:
        """Check if the API key has expired.

        Returns:
            bool: True if the key has expired, False otherwise.
        """
        if self.expires_at is None:
            return False
        return datetime.now(datetime.now().astimezone().tzinfo) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the API key is valid (active and not expired).

        Returns:
            bool: True if the key is valid, False otherwise.
        """
        return self.is_active and not self.is_expired

    @property
    def permission_list(self) -> List[str]:
        """Get permissions as a list.

        Returns:
            List[str]: List of permission strings.
        """
        return self.permissions or []

    def has_permission(self, permission: str) -> bool:
        """Check if the API key has a specific permission.

        Args:
            permission: The permission to check (e.g., "read:btc").

        Returns:
            bool: True if the key has the permission.
        """
        if not self.permissions:
            return False
        return permission in self.permissions

    def update_last_used(self) -> None:
        """Update the last_used_at timestamp to now."""
        self.last_used_at = datetime.now(datetime.now().astimezone().tzinfo)

    def set_expiry_days(self, days: int) -> None:
        """Set expiration date to a number of days from now.

        Args:
            days: Number of days until expiration.
        """
        self.expires_at = datetime.now(datetime.now().astimezone().tzinfo) + timedelta(days=days)

    def dict(self) -> dict:
        """Convert API key to dictionary (excludes hashed_key).

        Returns:
            dict: API key data without sensitive fields.
        """
        data = super().dict()
        # Remove sensitive fields
        data.pop("hashed_key", None)
        # Add computed properties
        data["is_expired"] = self.is_expired
        data["is_valid"] = self.is_valid
        data["permission_list"] = self.permission_list
        return data