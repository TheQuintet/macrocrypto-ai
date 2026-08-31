"""WebSocket connection manager for real-time price updates.

This module provides a connection manager for WebSocket clients,
handling connections, disconnections, and broadcasting messages.
"""

import logging
import json
from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketDisconnect

from app.core.config import settings

logger = logging.getLogger(settings.SERVICE_NAME)


class ConnectionManager:
    """Manage WebSocket connections and broadcast messages.

    Handles:
    - Client connections and disconnections
    - Message broadcasting to all clients
    - User-specific messaging
    - Connection tracking and cleanup
    """

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[int, List[WebSocket]] = {}
        self._lock = None  # Will be initialized if needed

    async def connect(self, websocket: WebSocket, user_id: Optional[int] = None) -> None:
        """Accept a WebSocket connection and register it.

        Args:
            websocket: The WebSocket connection.
            user_id: Optional user ID for authenticated connections.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)
            logger.info(f"WebSocket connected: user_id={user_id}, total={len(self.active_connections)}")
        else:
            logger.info(f"WebSocket connected (guest), total={len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, user_id: Optional[int] = None) -> None:
        """Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove.
            user_id: Optional user ID for cleanup.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

        logger.info(f"WebSocket disconnected, total={len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all connected clients.

        Args:
            message: The message to broadcast.
        """
        if not self.active_connections:
            return

        data = json.dumps(message)
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def send_to_user(self, user_id: int, message: Dict[str, Any]) -> None:
        """Send a message to a specific user's connections.

        Args:
            user_id: The user ID to send to.
            message: The message to send.
        """
        if user_id not in self.user_connections:
            return

        data = json.dumps(message)
        disconnected = []

        for connection in self.user_connections[user_id]:
            try:
                await connection.send_text(data)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, user_id)

    async def broadcast_price_update(self, price_data: Dict[str, Any]) -> None:
        """Broadcast a price update to all connected clients.

        Args:
            price_data: The price update data.
        """
        message = {
            "type": "price_update",
            "data": price_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.broadcast(message)

    async def send_alert(self, alert_data: Dict[str, Any]) -> None:
        """Broadcast an alert to all connected clients.

        Args:
            alert_data: The alert data.
        """
        message = {
            "type": "alert",
            "data": alert_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.broadcast(message)

    async def send_heartbeat(self, websocket: WebSocket) -> None:
        """Send a heartbeat message to keep the connection alive.

        Args:
            websocket: The WebSocket connection.
        """
        try:
            await websocket.send_text(json.dumps({"type": "ping"}))
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")

    def get_connection_count(self) -> int:
        """Get the total number of active connections.

        Returns:
            int: Number of active connections.
        """
        return len(self.active_connections)

    def get_user_connection_count(self, user_id: int) -> int:
        """Get the number of connections for a specific user.

        Args:
            user_id: The user ID.

        Returns:
            int: Number of connections for the user.
        """
        return len(self.user_connections.get(user_id, []))

    def is_connected(self, websocket: WebSocket) -> bool:
        """Check if a WebSocket is still connected.

        Args:
            websocket: The WebSocket connection.

        Returns:
            bool: True if connected, False otherwise.
        """
        return websocket in self.active_connections


# ============================================
# SINGLETON INSTANCE
# ============================================

manager = ConnectionManager()