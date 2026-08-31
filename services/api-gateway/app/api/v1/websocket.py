"""WebSocket endpoints for real-time price updates.

This module provides WebSocket endpoints for clients to receive
real-time BTC price updates and alerts.
"""

import json
import logging
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Query, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.websocket_manager import manager
from app.core.security import decode_token, verify_token_type
from app.core.database import get_db
from app.models.user import User, UserStatus

logger = logging.getLogger(settings.SERVICE_NAME)

# ============================================
# ROUTER
# ============================================

router = APIRouter(tags=["WebSocket"])
security = HTTPBearer()


# ============================================
# WEBSOCKET ENDPOINT
# ============================================

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT token for authentication"),
    db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for real-time price updates.

    Connect to receive real-time BTC price updates and alerts.
    Authentication is optional but recommended for user-specific features.

    Query Parameters:
        token: JWT access token (optional)

    Message Format (Server -> Client):
        {
            "type": "price_update",
            "data": {
                "symbol": "BTC",
                "price": 45000.00,
                "change_24h_percent": 2.5,
                "volume": 1500000,
                "timestamp": "2026-08-27T..."
            },
            "timestamp": "2026-08-27T..."
        }

    Heartbeat (Server -> Client):
        {
            "type": "ping"
        }
    """
    user_id = None
    user = None

    # Authenticate user if token is provided
    if token:
        try:
            payload = decode_token(token)
            verify_token_type(payload, "access")

            user_id = payload.get("sub")
            if user_id:
                user = db.query(User).filter(
                    User.id == user_id,
                    User.status == UserStatus.ACTIVE
                ).first()

                if user:
                    logger.info(f"WebSocket authenticated: user_id={user_id}, username={user.username}")
                else:
                    logger.warning(f"WebSocket authentication failed: user_id={user_id} not found or inactive")
                    user_id = None
        except Exception as e:
            logger.warning(f"WebSocket authentication error: {e}")
            user_id = None

    # Accept connection
    await manager.connect(websocket, user_id)

    try:
        # Send welcome message
        welcome_message = {
            "type": "connection",
            "status": "connected",
            "user_id": user_id,
            "message": "Connected to MacroCrypto AI WebSocket",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await websocket.send_text(json.dumps(welcome_message))

        # Send current price on connection (if available)
        # This would be fetched from cache or data service
        # For now, we'll just send a placeholder
        current_price = {
            "type": "price_update",
            "data": {
                "symbol": "BTC",
                "price": 45000.00,
                "change_24h_percent": 0.0,
                "volume": 0,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await websocket.send_text(json.dumps(current_price))

        # Main loop - receive messages from client
        while True:
            try:
                # Wait for message from client with timeout
                # This allows us to send heartbeats if needed
                data = await websocket.receive_text()

                # Process client messages (if any)
                try:
                    message = json.loads(data)
                    message_type = message.get("type")

                    if message_type == "ping":
                        # Respond to ping with pong
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    elif message_type == "subscribe":
                        # Client wants to subscribe to specific updates
                        # For now, we just acknowledge
                        await websocket.send_text(json.dumps({
                            "type": "subscription",
                            "status": "subscribed",
                            "message": "Subscribed to all updates",
                        }))
                    elif message_type == "unsubscribe":
                        await websocket.send_text(json.dumps({
                            "type": "subscription",
                            "status": "unsubscribed",
                            "message": "Unsubscribed from updates",
                        }))
                    else:
                        logger.debug(f"Unknown message type: {message_type}")

                except json.JSONDecodeError:
                    logger.debug(f"Invalid JSON from client: {data[:100]}")

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: user_id={user_id}")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user_id={user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Clean up connection
        manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket connection closed: user_id={user_id}")


# ============================================
# WEBSOCKET STATUS ENDPOINT
# ============================================

@router.get("/ws/status")
async def websocket_status():
    """
    Get WebSocket connection status.

    Returns:
        dict: Connection statistics.
    """
    return {
        "active_connections": manager.get_connection_count(),
        "user_connections": len(manager.user_connections),
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }