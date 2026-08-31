"""Integration tests for authentication endpoints."""

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

    def test_full_auth_flow(self, client):
        """Test complete authentication flow: register → login → me → refresh → logout."""
        unique = str(int(time.time() * 1000000))

        # 1. Register
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"flowuser{unique}@example.com",
                "username": f"flowuser{unique}",
                "password": "TestPass123",
                "full_name": "Flow User"
            }
        )
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["email"] == f"flowuser{unique}@example.com"
        assert user_data["username"] == f"flowuser{unique}"
        assert user_data["status"] == "pending"
        user_id = user_data["id"]

        # 2. Login should fail (pending user)
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": f"flowuser{unique}",
                "password": "TestPass123"
            }
        )
        assert login_response.status_code == 403
        assert "pending verification" in login_response.text

        # 3. Manually verify user in database
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            user.status = UserStatus.ACTIVE
            user.is_email_verified = True
            db.commit()
        finally:
            db.close()

        # 4. Login again (should work)
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": f"flowuser{unique}",
                "password": "TestPass123"
            }
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # 5. Get current user
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_response.status_code == 200
        user_info = me_response.json()
        assert user_info["username"] == f"flowuser{unique}"
        assert user_info["status"] == "active"

        # 6. Refresh token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        new_access_token = new_tokens["access_token"]

        # 7. Verify new token works
        me_response2 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert me_response2.status_code == 200
        assert me_response2.json()["username"] == f"flowuser{unique}"

        # 8. Change password
        change_response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {new_access_token}"},
            json={
                "current_password": "TestPass123",
                "new_password": "NewPass456"
            }
        )
        assert change_response.status_code == 200
        assert "Password changed successfully" in change_response.text

        # 9. Login with new password
        login_response2 = client.post(
            "/api/v1/auth/login",
            json={
                "username": f"flowuser{unique}",
                "password": "NewPass456"
            }
        )
        assert login_response2.status_code == 200

        # 10. Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert logout_response.status_code == 200
        assert "Successfully logged out" in logout_response.text

    def test_invalid_login(self, client):
        """Test login with invalid credentials."""
        # Register a user
        unique = str(int(time.time() * 1000000))
        client.post(
            "/api/v1/auth/register",
            json={
                "email": f"invalid{unique}@example.com",
                "username": f"invalid{unique}",
                "password": "TestPass123",
                "full_name": "Invalid User"
            }
        )

        # Login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": f"invalid{unique}",
                "password": "WrongPassword"
            }
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.text

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert "Not authenticated" in response.text

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
        assert "Could not validate credentials" in response.text