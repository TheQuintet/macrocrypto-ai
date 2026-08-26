"""Unit tests for authentication endpoints."""

import pytest
import time
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.user import User, UserStatus, UserRole
from app.core.security import get_password_hash


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    db = SessionLocal()
    try:
        yield db
        # Rollback any pending transaction after test
        db.rollback()
    finally:
        db.close()


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_register_success(self, client):
        """Test successful user registration."""
        unique = str(int(time.time()))
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"newuser{unique}@example.com",
                "username": f"newuser{unique}",
                "password": "TestPass123",
                "full_name": "New User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == f"newuser{unique}@example.com"
        assert data["username"] == f"newuser{unique}"
        assert data["full_name"] == "New User"
        assert data["role"] == "user"
        assert data["status"] == "pending"
        assert data["is_email_verified"] is False

    def test_register_duplicate_email(self, client, db_session):
        """Test registration with duplicate email."""
        unique = str(int(time.time()))
        # Create a user first with unique email
        user = User(
            email=f"dupemail{unique}@example.com",
            username=f"dupuser{unique}",
            hashed_password=get_password_hash("TestPass123"),
            full_name="Duplicate User",
            role=UserRole.USER,
            status=UserStatus.PENDING,
            is_email_verified=False,
        )
        db_session.add(user)
        db_session.commit()

        # Try to register with same email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"dupemail{unique}@example.com",
                "username": f"newuser{unique}",
                "password": "TestPass123",
                "full_name": "New User"
            }
        )
        assert response.status_code == 400
        assert "Email already registered" in response.text

    def test_register_invalid_username(self, client):
        """Test registration with invalid username."""
        unique = str(int(time.time()))
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"newuser{unique}@example.com",
                "username": "invalid!@#",
                "password": "TestPass123",
                "full_name": "New User"
            }
        )
        assert response.status_code == 400
        assert "Username must be 3-30 characters" in response.text

    def test_login_success(self, client, db_session):
        """Test successful login."""
        unique = str(int(time.time()))
        # Create an active user
        user = User(
            email=f"login{unique}@example.com",
            username=f"loginuser{unique}",
            hashed_password=get_password_hash("TestPass123"),
            full_name="Login User",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            is_email_verified=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": f"loginuser{unique}",
                "password": "TestPass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_pending_user(self, client, db_session):
        """Test login with pending user."""
        unique = str(int(time.time()))
        # Create a pending user
        user = User(
            email=f"pending{unique}@example.com",
            username=f"pendinguser{unique}",
            hashed_password=get_password_hash("TestPass123"),
            full_name="Pending User",
            role=UserRole.USER,
            status=UserStatus.PENDING,
            is_email_verified=False,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": f"pendinguser{unique}",
                "password": "TestPass123"
            }
        )
        assert response.status_code == 403
        assert "pending verification" in response.text

    def test_login_wrong_password(self, client, db_session):
        """Test login with wrong password."""
        unique = str(int(time.time()))
        # Create an active user
        user = User(
            email=f"wrongpass{unique}@example.com",
            username=f"wrongpass{unique}",
            hashed_password=get_password_hash("TestPass123"),
            full_name="Wrong Password User",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            is_email_verified=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": f"wrongpass{unique}",
                "password": "WrongPassword"
            }
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.text

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "TestPass123"
            }
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.text

    def test_me_endpoint_authenticated(self, client, db_session):
        """Test getting current user with valid token."""
        unique = str(int(time.time()))
        # Create an active user and get token
        user = User(
            email=f"meuser{unique}@example.com",
            username=f"meuser{unique}",
            hashed_password=get_password_hash("TestPass123"),
            full_name="Me User",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            is_email_verified=True,
        )
        db_session.add(user)
        db_session.commit()

        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": f"meuser{unique}",
                "password": "TestPass123"
            }
        )
        token = login_response.json()["access_token"]

        # Get user info
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == f"meuser{unique}"
        assert data["email"] == f"meuser{unique}@example.com"
        assert data["status"] == "active"

    def test_me_endpoint_unauthenticated(self, client):
        """Test getting current user without token."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_me_endpoint_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
        assert "Could not validate credentials" in response.text

    def test_refresh_token_success(self, client, db_session):
        """Test successful token refresh."""
        unique = str(int(time.time()))
        # Create an active user
        user = User(
            email=f"refresh{unique}@example.com",
            username=f"refreshuser{unique}",
            hashed_password=get_password_hash("TestPass123"),
            full_name="Refresh User",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            is_email_verified=True,
        )
        db_session.add(user)
        db_session.commit()

        # Login to get refresh token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": f"refreshuser{unique}",
                "password": "TestPass123"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        assert response.status_code == 401
        assert "Could not validate credentials" in response.text

    def test_logout(self, client, db_session):
        """Test logout endpoint."""
        unique = str(int(time.time()))
        # Create an active user and get token
        user = User(
            email=f"logout{unique}@example.com",
            username=f"logoutuser{unique}",
            hashed_password=get_password_hash("TestPass123"),
            full_name="Logout User",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            is_email_verified=True,
        )
        db_session.add(user)
        db_session.commit()

        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": f"logoutuser{unique}",
                "password": "TestPass123"
            }
        )
        token = login_response.json()["access_token"]

        # Logout
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"
        assert "user_id" in data