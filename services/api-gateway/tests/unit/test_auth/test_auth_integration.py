"""Integration tests for authentication flow."""

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


@pytest.fixture
def db_session():
    """Create database session for tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


class TestAuthIntegration:
    """Integration tests for authentication flow."""

    def test_full_auth_flow(self, client, db_session):
        """Test the full authentication flow: register → login → me."""
        # Use unique email/username to avoid conflicts
        unique = str(int(time.time()))
        email = f"flowuser{unique}@example.com"
        username = f"flowuser{unique}"

        # 1. Register
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": username,
                "password": "TestPass123",
                "full_name": "Flow User"
            }
        )
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]

        # 2. Verify the user in database
        user = db_session.query(User).filter(User.id == user_id).first()
        assert user is not None
        user.status = UserStatus.ACTIVE
        user.is_email_verified = True
        db_session.commit()

        # 3. Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": username,
                "password": "TestPass123"
            }
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        access_token = login_data["access_token"]

        # 4. Get current user
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["username"] == username
        assert me_response.json()["email"] == email
        assert me_response.json()["status"] == "active"