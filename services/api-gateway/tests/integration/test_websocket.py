"""Integration tests for WebSocket functionality."""

import pytest
import time
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

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


@pytest.fixture
def auth_token(client, db_session):
    """Create a user and return auth token."""
    unique = str(int(time.time() * 1000000))
    username = f"wsuser{unique}"
    email = f"ws{unique}@example.com"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": "TestPass123",
            "full_name": "WS User"
        }
    )
    user_id = register_response.json()["id"]

    user = db_session.query(User).filter(User.id == user_id).first()
    user.status = UserStatus.ACTIVE
    user.is_email_verified = True
    db_session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": username,
            "password": "TestPass123"
        }
    )
    return login_response.json()["access_token"]


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""

    def test_websocket_status(self, client):
        """Test WebSocket status endpoint."""
        response = client.get("/ws/status")
        assert response.status_code == 200
        data = response.json()
        assert "active_connections" in data
        assert "user_connections" in data
        assert "status" in data
        assert data["status"] == "operational"

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection."""
        try:
            import websockets
        except ImportError:
            pytest.skip("websockets module not installed")

        import asyncio

        try:
            async with websockets.connect("ws://localhost:8000/ws") as websocket:
                # Receive welcome message
                response = await websocket.recv()
                data = json.loads(response)
                assert data["type"] == "connection"
                assert data["status"] == "connected"
                assert "message" in data

                # Receive initial price update
                response = await websocket.recv()
                data = json.loads(response)
                assert data["type"] == "price_update"

                # Send ping
                await websocket.send(json.dumps({"type": "ping"}))
                response = await websocket.recv()
                data = json.loads(response)
                assert data["type"] == "pong"

        except ConnectionRefusedError:
            pytest.skip("WebSocket server not available")

    @pytest.mark.asyncio
    async def test_websocket_authenticated(self, auth_token):
        """Test authenticated WebSocket connection."""
        try:
            import websockets
        except ImportError:
            pytest.skip("websockets module not installed")

        import asyncio

        try:
            async with websockets.connect(f"ws://localhost:8000/ws?token={auth_token}") as websocket:
                # Receive welcome message
                response = await websocket.recv()
                data = json.loads(response)
                assert data["type"] == "connection"
                assert data["status"] == "connected"
                assert "user_id" in data

                # Receive initial price update
                response = await websocket.recv()
                data = json.loads(response)
                assert data["type"] == "price_update"

        except ConnectionRefusedError:
            pytest.skip("WebSocket server not available")