"""
Unit tests for HistoryService.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from app.services.history_service import HistoryService


class TestHistoryService:
    """Test suite for HistoryService."""

    def test_initialization(self):
        """Test HistoryService initialization."""
        service = HistoryService()
        assert hasattr(service, 'get_daily_candles')
        assert callable(service.get_daily_candles)

    @pytest.mark.asyncio
    async def test_get_daily_candles(self):
        """Test getting daily candles."""
        service = HistoryService()

        # ✅ Create proper mock response
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value=[
            [1704067200000, "42000.00", "43000.00", "41500.00", "42500.00", "1000.00"],
            [1704153600000, "42500.00", "43500.00", "42000.00", "43000.00", "1100.00"],
        ])
        mock_response.raise_for_status = MagicMock()

        # ✅ Mock the client's get method
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # ✅ Patch the AsyncClient class
        with patch('httpx.AsyncClient', return_value=MagicMock()) as mock_httpx_client:
            mock_httpx_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service.get_daily_candles(limit=8)

            # Should return DailyCandle objects
            assert len(result) == 2
            assert result[0].close == 42500.0
            assert result[1].close == 43000.0

    @pytest.mark.asyncio
    async def test_get_daily_candles_timeout(self):
        """Test getting daily candles with timeout."""
        service = HistoryService()

        # ✅ Mock the client to raise timeout
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        with patch('httpx.AsyncClient', return_value=MagicMock()) as mock_httpx_client:
            mock_httpx_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service.get_daily_candles(limit=8)

            # Should return empty list on timeout
            assert result == []

    @pytest.mark.asyncio
    async def test_get_daily_candles_http_error(self):
        """Test getting daily candles with HTTP error."""
        service = HistoryService()

        # ✅ Mock the client to raise HTTP error
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
            "404 Not Found", 
            request=MagicMock(), 
            response=mock_response
        ))

        with patch('httpx.AsyncClient', return_value=MagicMock()) as mock_httpx_client:
            mock_httpx_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service.get_daily_candles(limit=8)

            # Should return empty list on HTTP error
            assert result == []