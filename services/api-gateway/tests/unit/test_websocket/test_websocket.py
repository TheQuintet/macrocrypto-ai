"""Unit tests for WebSocket functionality."""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.core.websocket_manager import manager


class TestWebSocketManager:
    """Test WebSocket manager functionality."""

    @pytest.mark.asyncio
    async def test_connect(self):
        """Test WebSocket connection."""
        mock_websocket = AsyncMock()
        await manager.connect(mock_websocket, user_id=1)
        assert len(manager.active_connections) == 1
        assert 1 in manager.user_connections
        assert len(manager.user_connections[1]) == 1
        # Cleanup
        manager.disconnect(mock_websocket, user_id=1)

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test WebSocket disconnection."""
        mock_websocket = AsyncMock()
        await manager.connect(mock_websocket, user_id=1)
        # Verify connection was added
        assert len(manager.active_connections) == 1
        assert mock_websocket in manager.active_connections
        
        # Disconnect
        manager.disconnect(mock_websocket, user_id=1)
        assert len(manager.active_connections) == 0
        assert 1 not in manager.user_connections

    @pytest.mark.asyncio
    async def test_disconnect_guest(self):
        """Test WebSocket disconnection for guest user."""
        mock_websocket = AsyncMock()
        await manager.connect(mock_websocket)  # No user_id
        assert len(manager.active_connections) == 1
        
        manager.disconnect(mock_websocket)  # No user_id
        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting messages."""
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        await manager.connect(mock_websocket1)
        await manager.connect(mock_websocket2)
        
        await manager.broadcast({"test": "message"})
        
        mock_websocket1.send_text.assert_called_once()
        mock_websocket2.send_text.assert_called_once()
        # Cleanup
        manager.disconnect(mock_websocket1)
        manager.disconnect(mock_websocket2)

    @pytest.mark.asyncio
    async def test_send_to_user(self):
        """Test sending message to specific user."""
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        await manager.connect(mock_websocket1, user_id=1)
        await manager.connect(mock_websocket2, user_id=2)
        
        await manager.send_to_user(1, {"test": "message"})
        
        mock_websocket1.send_text.assert_called_once()
        mock_websocket2.send_text.assert_not_called()
        # Cleanup
        manager.disconnect(mock_websocket1, user_id=1)
        manager.disconnect(mock_websocket2, user_id=2)

    @pytest.mark.asyncio
    async def test_broadcast_price_update(self):
        """Test broadcasting price update."""
        mock_websocket = AsyncMock()
        await manager.connect(mock_websocket)
        
        price_data = {
            "symbol": "BTC",
            "price": 45000.00,
            "change_24h_percent": 2.5
        }
        await manager.broadcast_price_update(price_data)
        
        # Verify the message was sent
        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "price_update"
        assert message["data"]["symbol"] == "BTC"
        assert message["data"]["price"] == 45000.00
        # Cleanup
        manager.disconnect(mock_websocket)

    @pytest.mark.asyncio
    async def test_send_alert(self):
        """Test sending alert."""
        mock_websocket = AsyncMock()
        await manager.connect(mock_websocket)
        
        alert_data = {
            "alert_id": 1,
            "message": "BTC price alert",
            "type": "price_alert"
        }
        await manager.send_alert(alert_data)
        
        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "alert"
        assert message["data"]["alert_id"] == 1
        # Cleanup
        manager.disconnect(mock_websocket)

    def test_get_connection_count(self):
        """Test getting connection count."""
        count = manager.get_connection_count()
        assert count >= 0

    def test_get_user_connection_count(self):
        """Test getting user connection count."""
        count = manager.get_user_connection_count(1)
        assert count >= 0


class TestWebSocketStatus:
    """Test WebSocket status endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_websocket_status(self, client):
        """Test WebSocket status endpoint."""
        response = client.get("/ws/status")
        assert response.status_code == 200
        data = response.json()
        assert "active_connections" in data
        assert "user_connections" in data
        assert "status" in data
        assert data["status"] == "operational"