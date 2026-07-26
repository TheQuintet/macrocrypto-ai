"""Unit tests for BinanceCollector."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.collectors.binance import BinanceCollector


class TestBinanceCollector:
    """Test suite for BinanceCollector."""

    def test_initialization(self):
        collector = BinanceCollector()
        assert collector.base_url is not None
        assert collector.timeout == 10.0

    @pytest.mark.asyncio
    async def test_get_24hr_ticker_success(self):
        collector = BinanceCollector()

        # ✅ Create proper mock response
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value={
            "symbol": "BTCUSDT",
            "priceChange": "1000.00",
            "priceChangePercent": "2.27",
            "lastPrice": "45000.00",
            "openPrice": "44000.00",
            "highPrice": "46000.00",
            "lowPrice": "43500.00",
            "volume": "1000.00",
            "quoteVolume": "45000000.00",
        })
        mock_response.raise_for_status = MagicMock()

        # ✅ Mock the client's get method to return the response
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # ✅ Patch the AsyncClient class
        with patch('httpx.AsyncClient', return_value=MagicMock()) as mock_httpx_client:
            mock_httpx_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx_client.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # ✅ Reassign the client in collector
            collector.client = mock_client

            result = await collector.get_24hr_ticker("BTCUSDT")
            
            assert result["symbol"] == "BTCUSDT"
            assert result["last_price"] == 45000.0
            assert result["price_change_percent"] == 2.27

    @pytest.mark.asyncio
    async def test_get_24hr_ticker_failure(self):
        collector = BinanceCollector()

        # ✅ Mock the client to raise an exception
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=Exception("API Error"))

        collector.client = mock_client

        result = await collector.get_24hr_ticker("BTCUSDT")
        
        assert result["source"] == "binance_rest_dummy"
        assert result["last_price"] == 0.0

    @pytest.mark.asyncio
    async def test_close(self):
        collector = BinanceCollector()
        collector.client = MagicMock()
        collector.client.aclose = AsyncMock()
        
        await collector.close()
        collector.client.aclose.assert_called_once()