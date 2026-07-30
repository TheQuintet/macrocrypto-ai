"""
Integration test for WebSocket connection.

Validates:
- WebSocket connection
- Subscription to BTC/USDT ticker
- Receiving price updates
"""

import asyncio
import json
import pytest
import socket
import websockets


def is_internet_available():
    """Check if Binance WebSocket is reachable."""
    try:
        socket.gethostbyname("stream.binance.com")
        return True
    except socket.gaierror:
        return False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection to Binance stream."""

    # ✅ Skip test if DNS resolution fails
    if not is_internet_available():
        pytest.skip("Binance WebSocket not reachable (DNS resolution failed)")

    ws_url = "wss://stream.binance.com:9443/ws"

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected")

            # Subscribe to BTC/USDT ticker
            subscribe_msg = {
                "method": "SUBSCRIBE",
                "params": ["btcusdt@ticker"],
                "id": 1
            }
            await websocket.send(json.dumps(subscribe_msg))
            print("📤 Subscribed to btcusdt@ticker")

            # Wait for subscription response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            response_data = json.loads(response)
            print(f"📥 Subscription response: {response_data}")

            assert response_data.get("result") is None
            assert response_data.get("id") == 1

            # Wait for a price update
            price_data = await asyncio.wait_for(websocket.recv(), timeout=10)
            price_data_parsed = json.loads(price_data)
            print(f"💰 Price data received")

            # Check that price data contains expected fields
            assert "c" in price_data_parsed  # Current price
            assert "s" in price_data_parsed  # Symbol
            assert price_data_parsed["s"] == "BTCUSDT"

            await websocket.close()
            print("✅ WebSocket test completed successfully")

    except asyncio.TimeoutError:
        pytest.fail("Timeout waiting for WebSocket response")
    except Exception as e:
        pytest.fail(f"WebSocket connection failed: {e}")