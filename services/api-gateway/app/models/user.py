"""User model for authentication and user management.

This module defines the User model with fields for authentication,
authorization, and user profile information.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Enum, String, Table, Text
from sqlalchemy.orm import relationship

from app.models.base import Base

import enum


class UserRole(str, enum.Enum):
    """User roles for authorization.

    - ADMIN: Full system access
    - USER: Standard user access (default)
    - GUEST: Limited read-only access
    """

    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class UserStatus(str, enum.Enum):
    """User account status.

    - ACTIVE: Normal active account
    - INACTIVE: Disabled account (cannot login)
    - SUSPENDED: Temporarily suspended
    - PENDING: Awaiting email verification
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(Base):
    """User model for authentication and profile management.

    Attributes:
        email: Unique email address for login
        username: Unique username for display
        hashed_password: Bcrypt-hashed password
        full_name: User's full name (optional)
        role: User's role (admin/user/guest)
        status: Account status (active/inactive/suspended/pending)
        is_email_verified: Whether email has been verified
        last_login: Timestamp of last successful login
        profile: JSON field for additional profile data
        api_keys: Relationship to APIKey model
        exports: Relationship to ExportHistory model
    """

    __tablename__ = "users"

    # Basic information
    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique email address for login",
    )
    username = Column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique username for display",
    )
    hashed_password = Column(
        String(255),
        nullable=False,
        doc="Bcrypt-hashed password",
    )
    full_name = Column(
        String(200),
        nullable=True,
        doc="User's full name (optional)",
    )

    # Authorization
    role = Column(
        Enum(UserRole),
        default=UserRole.USER,
        nullable=False,
        doc="User's role for authorization",
    )
    status = Column(
        Enum(UserStatus),
        default=UserStatus.PENDING,
        nullable=False,
        doc="Account status",
    )
    is_email_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether email has been verified",
    )

    # Timestamps
    last_login = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of last successful login",
    )
    email_verified_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when email was verified",
    )
    password_changed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when password was last changed",
    )

    # Additional data
    profile = Column(
        Text,
        nullable=True,
        doc="JSON field for additional profile data",
    )

    # Relationships
    api_keys = relationship(
        "APIKey",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
        doc="User's API keys",
    )
    exports = relationship(
        "ExportHistory",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
        doc="User's export history",
    )

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    def dict(self) -> dict:
        """Convert user to dictionary (excludes sensitive data).

        Returns:
            dict: User data without sensitive fields.
        """
        data = super().dict()
        # Remove sensitive fields
        data.pop("hashed_password", None)
        return data

    @property
    def is_active(self) -> bool:
        """Check if user account is active.

        Returns:
            bool: True if user status is ACTIVE, False otherwise.
        """
        return self.status == UserStatus.ACTIVE

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role.

        Returns:
            bool: True if user role is ADMIN, False otherwise.
        """
        return self.role == UserRole.ADMIN

    @property
    def display_name(self) -> str:
        """Get user's display name.

        Returns:
            str: Full name if available, otherwise username.
        """
        return self.full_name or self.username