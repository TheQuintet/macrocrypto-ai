"""Unit tests for User model."""

import pytest
from datetime import datetime, timedelta

from app.models.user import User, UserRole, UserStatus


class TestUserModel:
    """Test User model functionality."""

    def test_create_user(self):
        """Test creating a user with required fields."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password_here",
            full_name="Test User"
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.hashed_password == "hashed_password_here"
        assert user.full_name == "Test User"
        assert user.role == UserRole.USER  # Default
        assert user.status == UserStatus.PENDING  # Default
        assert user.is_email_verified is False
        assert user.is_active is False  # PENDING means not active

    def test_user_defaults(self):
        """Test default values for User model."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password_here"
        )
        assert user.role == UserRole.USER
        assert user.status == UserStatus.PENDING
        assert user.is_email_verified is False
        assert user.full_name is None

    def test_user_properties(self):
        """Test User model properties."""
        # Active user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password_here",
            status=UserStatus.ACTIVE,
            role=UserRole.ADMIN
        )
        assert user.is_active is True
        assert user.is_admin is True
        assert user.display_name == "testuser"

        # User with full name
        user.full_name = "Test User"
        assert user.display_name == "Test User"

        # Inactive user
        user.status = UserStatus.INACTIVE
        assert user.is_active is False

    def test_user_roles(self):
        """Test different user roles."""
        admin = User(
            email="admin@example.com",
            username="admin",
            hashed_password="hashed",
            role=UserRole.ADMIN
        )
        assert admin.is_admin is True

        regular = User(
            email="user@example.com",
            username="user",
            hashed_password="hashed",
            role=UserRole.USER
        )
        assert regular.is_admin is False

        guest = User(
            email="guest@example.com",
            username="guest",
            hashed_password="hashed",
            role=UserRole.GUEST
        )
        assert guest.is_admin is False

    def test_user_dict_excludes_sensitive_data(self):
        """Test dict() method excludes hashed_password."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="secret_hash"
        )
        data = user.dict()
        assert "hashed_password" not in data
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"

    def test_user_repr(self):
        """Test string representation of User."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed"
        )
        repr_str = repr(user)
        assert "User" in repr_str
        assert "testuser" in repr_str
        assert "test@example.com" in repr_str