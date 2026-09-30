"""Tests for the WebSocket connection manager."""

import json
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocketDisconnect

from app.core.websocket_manager import ConnectionManager, manager


@pytest.fixture
def connection_manager():
    """Create a fresh connection manager for each test."""
    return ConnectionManager()


@pytest.fixture
def websocket():
    """Create a mock WebSocket."""
    mock = AsyncMock()
    return mock


class TestConnectionManagerInitialization:
    """Test ConnectionManager initialization."""

    def test_initial_state(self, connection_manager):
        """Test manager starts without connections."""
        assert connection_manager.active_connections == []
        assert connection_manager.user_connections == {}
        assert connection_manager._lock is None

    def test_singleton_manager_exists(self):
        """Test module-level manager instance exists."""
        assert isinstance(manager, ConnectionManager)


class TestConnection:
    """Test connection and disconnection handling."""

    @pytest.mark.asyncio
    async def test_connect_guest(self, connection_manager, websocket):
        """Test connecting a guest WebSocket."""
        await connection_manager.connect(websocket)

        websocket.accept.assert_awaited_once()
        assert websocket in connection_manager.active_connections
        assert connection_manager.get_connection_count() == 1
        assert connection_manager.user_connections == {}

    @pytest.mark.asyncio
    async def test_connect_authenticated_user(
        self,
        connection_manager,
        websocket,
    ):
        """Test connecting a WebSocket for a user."""
        await connection_manager.connect(websocket, user_id=123)

        websocket.accept.assert_awaited_once()
        assert websocket in connection_manager.active_connections
        assert connection_manager.user_connections[123] == [websocket]
        assert connection_manager.get_user_connection_count(123) == 1

    @pytest.mark.asyncio
    async def test_connect_multiple_connections_for_same_user(
        self,
        connection_manager,
    ):
        """Test multiple connections can belong to the same user."""
        websocket_one = AsyncMock()
        websocket_two = AsyncMock()

        await connection_manager.connect(websocket_one, user_id=123)
        await connection_manager.connect(websocket_two, user_id=123)

        assert connection_manager.get_connection_count() == 2
        assert connection_manager.get_user_connection_count(123) == 2
        assert connection_manager.user_connections[123] == [
            websocket_one,
            websocket_two,
        ]

    @pytest.mark.asyncio
    async def test_connect_user_id_zero_is_treated_as_guest(
        self,
        connection_manager,
        websocket,
    ):
        """Test that user ID zero follows the guest branch."""
        await connection_manager.connect(websocket, user_id=0)

        assert websocket in connection_manager.active_connections
        assert connection_manager.user_connections == {}

    def test_disconnect_guest(self, connection_manager, websocket):
        """Test disconnecting a guest connection."""
        connection_manager.active_connections.append(websocket)

        connection_manager.disconnect(websocket)

        assert websocket not in connection_manager.active_connections
        assert connection_manager.get_connection_count() == 0

    def test_disconnect_authenticated_user(
        self,
        connection_manager,
        websocket,
    ):
        """Test disconnecting a user's connection."""
        connection_manager.active_connections.append(websocket)
        connection_manager.user_connections[123] = [websocket]

        connection_manager.disconnect(websocket, user_id=123)

        assert websocket not in connection_manager.active_connections
        assert 123 not in connection_manager.user_connections

    def test_disconnect_user_with_remaining_connection(
        self,
        connection_manager,
    ):
        """Test disconnecting one of multiple user connections."""
        websocket_one = AsyncMock()
        websocket_two = AsyncMock()

        connection_manager.active_connections.extend(
            [websocket_one, websocket_two]
        )
        connection_manager.user_connections[123] = [
            websocket_one,
            websocket_two,
        ]

        connection_manager.disconnect(websocket_one, user_id=123)

        assert websocket_one not in connection_manager.active_connections
        assert websocket_two in connection_manager.active_connections
        assert connection_manager.user_connections[123] == [websocket_two]

    def test_disconnect_unknown_connection(
        self,
        connection_manager,
        websocket,
    ):
        """Test disconnecting an unregistered connection."""
        connection_manager.disconnect(websocket)

        assert connection_manager.active_connections == []
        assert connection_manager.user_connections == {}

    def test_disconnect_user_without_matching_connection(
        self,
        connection_manager,
        websocket,
    ):
        """Test user cleanup when connection is not in that user's list."""
        connection_manager.active_connections.append(websocket)
        connection_manager.user_connections[123] = []

        connection_manager.disconnect(websocket, user_id=123)

        assert websocket not in connection_manager.active_connections
        assert 123 in connection_manager.user_connections


class TestBroadcast:
    """Test broadcasting messages."""

    @pytest.mark.asyncio
    async def test_broadcast_with_no_connections(
        self,
        connection_manager,
    ):
        """Test broadcasting when there are no clients."""
        await connection_manager.broadcast({"type": "test"})

        assert connection_manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_broadcast_sends_json_to_all_connections(
        self,
        connection_manager,
    ):
        """Test message is sent to every active connection."""
        websocket_one = AsyncMock()
        websocket_two = AsyncMock()

        connection_manager.active_connections.extend(
            [websocket_one, websocket_two]
        )

        message = {
            "type": "test",
            "value": 123,
        }

        await connection_manager.broadcast(message)

        expected = json.dumps(message)

        websocket_one.send_text.assert_awaited_once_with(expected)
        websocket_two.send_text.assert_awaited_once_with(expected)

    @pytest.mark.asyncio
    async def test_broadcast_removes_disconnected_clients(
        self,
        connection_manager,
    ):
        """Test WebSocketDisconnect clients are removed."""
        working = AsyncMock()
        disconnected = AsyncMock()

        disconnected.send_text.side_effect = WebSocketDisconnect()

        connection_manager.active_connections.extend(
            [working, disconnected]
        )

        await connection_manager.broadcast({"type": "test"})

        working.send_text.assert_awaited_once()
        disconnected.send_text.assert_awaited_once()

        assert working in connection_manager.active_connections
        assert disconnected not in connection_manager.active_connections
        assert connection_manager.get_connection_count() == 1

    @pytest.mark.asyncio
    async def test_broadcast_removes_clients_with_send_errors(
        self,
        connection_manager,
    ):
        """Test clients raising unexpected errors are removed."""
        working = AsyncMock()
        failed = AsyncMock()

        failed.send_text.side_effect = RuntimeError("connection failed")

        connection_manager.active_connections.extend(
            [working, failed]
        )

        await connection_manager.broadcast({"type": "test"})

        assert working in connection_manager.active_connections
        assert failed not in connection_manager.active_connections
        assert connection_manager.get_connection_count() == 1


class TestSendToUser:
    """Test user-specific messaging."""

    @pytest.mark.asyncio
    async def test_send_to_unknown_user(
        self,
        connection_manager,
    ):
        """Test sending to a user with no connections."""
        await connection_manager.send_to_user(
            999,
            {"type": "test"},
        )

        assert connection_manager.user_connections == {}

    @pytest.mark.asyncio
    async def test_send_to_user_connections(
        self,
        connection_manager,
    ):
        """Test message is sent to all connections for a user."""
        websocket_one = AsyncMock()
        websocket_two = AsyncMock()

        connection_manager.user_connections[123] = [
            websocket_one,
            websocket_two,
        ]

        message = {
            "type": "private",
            "value": "hello",
        }

        await connection_manager.send_to_user(123, message)

        expected = json.dumps(message)

        websocket_one.send_text.assert_awaited_once_with(expected)
        websocket_two.send_text.assert_awaited_once_with(expected)

    @pytest.mark.asyncio
    async def test_send_to_user_removes_disconnected_connection(
        self,
        connection_manager,
    ):
        """Test disconnected user connections are cleaned up."""
        working = AsyncMock()
        disconnected = AsyncMock()

        disconnected.send_text.side_effect = WebSocketDisconnect()

        connection_manager.active_connections.extend(
            [working, disconnected]
        )
        connection_manager.user_connections[123] = [
            working,
            disconnected,
        ]

        await connection_manager.send_to_user(
            123,
            {"type": "test"},
        )

        assert working in connection_manager.active_connections
        assert disconnected not in connection_manager.active_connections
        assert connection_manager.user_connections[123] == [working]

    @pytest.mark.asyncio
    async def test_send_to_user_removes_connection_on_error(
        self,
        connection_manager,
    ):
        """Test user connections raising errors are removed."""
        working = AsyncMock()
        failed = AsyncMock()

        failed.send_text.side_effect = RuntimeError("send failed")

        connection_manager.active_connections.extend(
            [working, failed]
        )
        connection_manager.user_connections[123] = [
            working,
            failed,
        ]

        await connection_manager.send_to_user(
            123,
            {"type": "test"},
        )

        assert working in connection_manager.active_connections
        assert failed not in connection_manager.active_connections
        assert connection_manager.user_connections[123] == [working]


class TestMessageHelpers:
    """Test specialized message helpers."""

    @pytest.mark.asyncio
    async def test_broadcast_price_update(
        self,
        connection_manager,
        websocket,
    ):
        """Test price update message structure."""
        connection_manager.active_connections.append(websocket)

        price_data = {
            "symbol": "BTCUSDT",
            "price": 75000.0,
        }

        await connection_manager.broadcast_price_update(price_data)

        websocket.send_text.assert_awaited_once()

        sent_message = json.loads(
            websocket.send_text.await_args.args[0]
        )

        assert sent_message["type"] == "price_update"
        assert sent_message["data"] == price_data
        assert "timestamp" in sent_message
        assert sent_message["timestamp"]

    @pytest.mark.asyncio
    async def test_send_alert(
        self,
        connection_manager,
        websocket,
    ):
        """Test alert message structure."""
        connection_manager.active_connections.append(websocket)

        alert_data = {
            "alert_id": 42,
            "message": "BTC price threshold reached",
        }

        await connection_manager.send_alert(alert_data)

        websocket.send_text.assert_awaited_once()

        sent_message = json.loads(
            websocket.send_text.await_args.args[0]
        )

        assert sent_message["type"] == "alert"
        assert sent_message["data"] == alert_data
        assert "timestamp" in sent_message
        assert sent_message["timestamp"]

    @pytest.mark.asyncio
    async def test_send_heartbeat(
        self,
        connection_manager,
        websocket,
    ):
        """Test heartbeat sends ping message."""
        await connection_manager.send_heartbeat(websocket)

        websocket.send_text.assert_awaited_once_with(
            json.dumps({"type": "ping"})
        )

    @pytest.mark.asyncio
    async def test_send_heartbeat_handles_error(
        self,
        connection_manager,
        websocket,
    ):
        """Test heartbeat handles send errors without raising."""
        websocket.send_text.side_effect = RuntimeError(
            "connection closed"
        )

        await connection_manager.send_heartbeat(websocket)

        websocket.send_text.assert_awaited_once()


class TestConnectionQueries:
    """Test connection query methods."""

    def test_get_connection_count(
        self,
        connection_manager,
    ):
        """Test total connection count."""
        assert connection_manager.get_connection_count() == 0

        connection_manager.active_connections.extend(
            [AsyncMock(), AsyncMock(), AsyncMock()]
        )

        assert connection_manager.get_connection_count() == 3

    def test_get_user_connection_count(
        self,
        connection_manager,
    ):
        """Test user-specific connection count."""
        assert connection_manager.get_user_connection_count(123) == 0

        connection_manager.user_connections[123] = [
            AsyncMock(),
            AsyncMock(),
        ]

        assert connection_manager.get_user_connection_count(123) == 2

    def test_get_user_connection_count_for_unknown_user(
        self,
        connection_manager,
    ):
        """Test connection count for an unknown user."""
        assert connection_manager.get_user_connection_count(999) == 0

    def test_is_connected(
        self,
        connection_manager,
        websocket,
    ):
        """Test connection membership check."""
        assert connection_manager.is_connected(websocket) is False

        connection_manager.active_connections.append(websocket)

        assert connection_manager.is_connected(websocket) is True

        connection_manager.active_connections.remove(websocket)

        assert connection_manager.is_connected(websocket) is False

