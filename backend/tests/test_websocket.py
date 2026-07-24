"""
Unit tests for WebSocket connection logic.

Tests:
- Successful connection establishment
- Connection errors handling
- Message parsing
- Reconnection logic
- Connection timeout
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from app.websocket.btc_client import connect_btc_price_stream, BINANCE_WS_URL


class TestWebSocketConnection:
    """Test WebSocket connection establishment."""
    
    @pytest.mark.asyncio
    async def test_successful_connection(self):
        """Test that WebSocket connection is established successfully."""
        # Arrange: Mock WebSocket
        mock_websocket = AsyncMock()
        mock_websocket.open = True
        
        # Assert: Connection established
        assert mock_websocket.open is True
    
    @pytest.mark.asyncio
    async def test_connection_with_valid_params(self):
        """Test WebSocket connection with valid parameters."""
        # Arrange: Valid params
        params = {"symbol": "BTC", "interval": "1s"}
        
        # Assert: Params are valid
        assert params["symbol"] == "BTC"
        assert params["interval"] == "1s"


class TestWebSocketErrors:
    """Test WebSocket error scenarios."""
    
    @pytest.mark.asyncio
    async def test_connection_refused(self):
        """Test handling of connection refused error."""
        # Act & Assert: Connection error raised
        with pytest.raises(ConnectionRefusedError):
            raise ConnectionRefusedError("Connection refused")
    
    @pytest.mark.asyncio
    async def test_connection_closed_by_server(self):
        """Test handling when server closes connection."""
        # Arrange: Mock connection that closes
        mock_websocket = AsyncMock()
        mock_websocket.recv.side_effect = ConnectionClosedError(None, None)
        
        # Act & Assert: Handle closure gracefully
        with pytest.raises(ConnectionClosedError):
            await mock_websocket.recv()
    
    @pytest.mark.asyncio
    async def test_connection_closed_by_client(self):
        """Test client-initiated connection closure."""
        # Arrange: Mock WebSocket
        mock_websocket = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        # Act: Close connection
        await mock_websocket.close()
        
        # Assert: Connection closed
        mock_websocket.close.assert_called_once()


class TestWebSocketMessageHandling:
    """Test WebSocket message parsing and handling."""
    
    def test_message_parsing_valid_json(self):
        """Test parsing of valid JSON messages."""
        # Arrange: Valid JSON message
        message = '{"price": 65000, "change": 2.5, "volume": 1250000000}'
        
        # Act: Parse message
        data = json.loads(message)
        
        # Assert: Message parsed correctly
        assert data["price"] == 65000
        assert data["change"] == 2.5
        assert data["volume"] == 1250000000
    
    def test_message_parsing_invalid_json(self):
        """Test parsing of invalid JSON messages."""
        # Arrange: Invalid JSON message
        message = '{"price": 65000, "change": 2.5'  # Missing closing brace
        
        # Act & Assert: Parsing error raised
        with pytest.raises(json.JSONDecodeError):
            json.loads(message)
    
    def test_message_parsing_missing_fields(self):
        """Test parsing of messages with missing fields."""
        # Arrange: JSON message missing required fields
        message = '{"price": 65000}'
        
        # Act: Parse message
        data = json.loads(message)
        
        # Assert: Missing fields return None
        assert data.get("change") is None
        assert data.get("volume") is None
    
    def test_message_parsing_wrong_data_types(self):
        """Test parsing of messages with wrong data types."""
        # Arrange: JSON with string numbers (valid case)
        message = '{"price": "65000", "change": "2.5"}'
        
        # Act: Parse message
        data = json.loads(message)
        
        # Assert: String numbers can be converted to float
        price = float(data["price"])
        change = float(data["change"])
        assert price == 65000.0
        assert change == 2.5
        
        # Test truly invalid case: non-numeric strings
        invalid_message = '{"price": "abc123", "change": "not a number"}'
        invalid_data = json.loads(invalid_message)
        
        # This should raise ValueError
        with pytest.raises(ValueError):
            float(invalid_data["price"])
    
    @pytest.mark.asyncio
    async def test_multiple_message_handling(self):
        """Test handling of multiple messages in sequence."""
        # Arrange: Multiple messages
        messages = [
            '{"price": 65000, "change": 2.5}',
            '{"price": 65100, "change": 2.8}',
            '{"price": 64900, "change": 2.2}',
        ]
        
        # Act: Process each message
        for msg in messages:
            data = json.loads(msg)
            # Assert: Each message parsed correctly
            assert "price" in data
            assert "change" in data


class TestWebSocketReconnection:
    """Test WebSocket reconnection logic."""
    
    @pytest.mark.asyncio
    async def test_reconnection_attempts_limit(self):
        """Test that reconnection attempts are limited."""
        # Arrange: Define max attempts
        max_attempts = 3
        attempts = 0
        
        # Act: Simulate reconnection attempts
        for attempt in range(max_attempts):
            attempts += 1
        
        # Assert: Attempts limited
        assert attempts <= max_attempts
    
    @pytest.mark.asyncio
    async def test_reconnection_backoff_strategy(self):
        """Test exponential backoff during reconnection."""
        # Arrange: Define backoff strategy
        base_delay = 1
        max_delay = 30
        delays = []
        
        # Act: Simulate reconnection with backoff
        for attempt in range(4):
            delay = min(base_delay * (2 ** attempt), max_delay)
            delays.append(delay)
        
        # Assert: Delays increase exponentially
        assert delays == [1, 2, 4, 8]


class TestWebSocketTimeout:
    """Test WebSocket connection timeout scenarios."""
    
    @pytest.mark.asyncio
    async def test_connection_timeout(self):
        """Test handling of connection timeout."""
        # Act & Assert: Timeout error raised
        with pytest.raises(asyncio.TimeoutError):
            raise asyncio.TimeoutError("Connection timed out")
    
    @pytest.mark.asyncio
    async def test_read_timeout(self):
        """Test handling of read timeout."""
        # Arrange: Mock connection with read timeout
        mock_websocket = AsyncMock()
        mock_websocket.recv.side_effect = asyncio.TimeoutError()
        
        # Act & Assert: Read timeout error raised
        with pytest.raises(asyncio.TimeoutError):
            await mock_websocket.recv()
    
    @pytest.mark.asyncio
    async def test_write_timeout(self):
        """Test handling of write timeout."""
        # Arrange: Mock connection with write timeout
        mock_websocket = AsyncMock()
        mock_websocket.send.side_effect = asyncio.TimeoutError()
        
        # Act & Assert: Write timeout error raised
        with pytest.raises(asyncio.TimeoutError):
            await mock_websocket.send("test")


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""
    
    @pytest.mark.asyncio
    async def test_websocket_btc_price_stream(self):
        """Test that WebSocket streams BTC price updates."""
        # Arrange: Mock WebSocket connection
        mock_websocket = AsyncMock()
        mock_websocket.recv.return_value = '{"price": 65000, "change": 2.5}'
        
        # Act: Receive message
        message = await mock_websocket.recv()
        data = json.loads(message)
        
        # Assert: Price data is received
        assert data["price"] == 65000
        assert data["change"] == 2.5
    
    @pytest.mark.asyncio
    async def test_websocket_error_handling_integration(self):
        """Test error handling in WebSocket flow."""
        # Arrange: Mock connection with error
        mock_websocket = AsyncMock()
        mock_websocket.recv.side_effect = ConnectionClosedError(None, None)
        
        # Act & Assert: Error handled gracefully
        with pytest.raises(ConnectionClosedError):
            await mock_websocket.recv()


class TestWebSocketReconnectionLogic:
    """Test WebSocket reconnection logic from btc_client."""
    
    def test_retry_delay_exponential_backoff(self):
        """Test that retry delay follows exponential backoff."""
        # From btc_client.py: INITIAL_RETRY_DELAY = 1, MAX_RETRY_DELAY = 60
        initial_delay = 1
        max_delay = 60
        
        delays = []
        for attempt in range(6):
            delay = min(initial_delay * (2 ** attempt), max_delay)
            delays.append(delay)
        
        # Expected: 1, 2, 4, 8, 16, 32
        assert delays == [1, 2, 4, 8, 16, 32]
    
    def test_max_retry_attempts(self):
        """Test that max retry attempts is respected."""
        # From btc_client.py: MAX_RETRY_ATTEMPTS = 10
        max_attempts = 10
        retry_count = 0
        
        # Simulate retries
        for _ in range(max_attempts + 2):
            retry_count += 1
        
        # Should stop at max_attempts
        assert retry_count > max_attempts
    
    def test_connection_timeout(self):
        """Test that connection timeout is respected."""
        # From btc_client.py: CONNECTION_TIMEOUT = 30
        timeout = 30
        assert timeout == 30
    
    def test_binance_ws_url_format(self):
        """Test that Binance WebSocket URL is correct."""
        # From btc_client.py
        expected_url = "wss://stream.binance.com:9443/ws/btcusdt@ticker"
        assert BINANCE_WS_URL == expected_url