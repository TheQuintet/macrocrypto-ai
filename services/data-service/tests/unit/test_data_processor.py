"""
Unit tests for DataProcessor.
"""

import pytest
from app.services.data_processor import DataProcessor
from app.services.price_service import PriceService
from app.config import settings


class TestDataProcessor:
    """Test suite for DataProcessor."""

    def test_initialization(self):
        """Test DataProcessor initialization."""
        price_service = PriceService()
        processor = DataProcessor(price_service=price_service)
        
        assert processor.price_service is price_service

    def test_initialization_without_price_service(self):
        """Test DataProcessor initialization without PriceService."""
        processor = DataProcessor()
        
        assert processor.price_service is not None
        assert isinstance(processor.price_service, PriceService)

    def test_extract_binance_data(self):
        """Test extracting Binance data."""
        processor = DataProcessor()
        
        data = {
            "s": "BTCUSDT",
            "c": "45000.00",
            "o": "44000.00",
            "h": "46000.00",
            "l": "43500.00",
            "v": "1000.00",
            "q": "45000000.00",
            "P": "2.27",
            "p": "1000.00",
            "E": 1704787200000
        }
        
        result = processor._extract_binance_data(data)
        
        assert result["symbol"] == "BTCUSDT"
        assert result["price"] == 45000.0
        assert result["open"] == 44000.0
        assert result["high"] == 46000.0
        assert result["low"] == 43500.0
        assert result["volume"] == 1000.0
        assert result["quote_volume"] == 45000000.0
        assert result["change_24h"] == 2.27
        assert result["change_abs"] == 1000.0
        assert result["source"] == "binance_ws"

    def test_extract_binance_data_invalid_price(self):
        """Test extracting Binance data with invalid price."""
        processor = DataProcessor()
        
        data = {"c": "0"}
        result = processor._extract_binance_data(data)
        
        assert result is None

    def test_process_ticker_update(self):
        """Test processing ticker update."""
        price_service = PriceService()
        processor = DataProcessor(price_service=price_service)
        
        data = {
            "s": "BTCUSDT",
            "c": "45000.00",
            "P": "2.27",
            "h": "46000.00",
            "l": "43500.00",
            "v": "1000.00"
        }
        
        result = processor.process_ticker_update(data)
        
        assert result is True
        assert price_service.get_price() == 45000.0

    def test_process_ticker_update_missing_fields(self):
        """Test processing ticker update with missing fields."""
        processor = DataProcessor()
        
        data = {}
        result = processor.process_ticker_update(data)
        
        assert result is False

    def test_process_price_data(self):
        """Test processing normalized price data."""
        price_service = PriceService()
        processor = DataProcessor(price_service=price_service)
        
        price_data = {
            "symbol": "BTCUSDT",
            "price": 45000.0,
            "change_24h": 2.27,
            "high": 46000.0,
            "low": 43500.0,
            "volume": 1000.0
        }
        
        result = processor.process_price_data(price_data)
        
        assert result is True
        assert price_service.get_price() == 45000.0

    def test_process_price_data_missing_fields(self):
        """Test processing normalized price data with missing fields."""
        processor = DataProcessor()
        
        price_data = {"price": 45000.0}  # Missing symbol
        result = processor.process_price_data(price_data)
        
        assert result is False

    def test_process_multiple(self):
        """Test processing multiple ticker updates."""
        processor = DataProcessor()
        
        data_list = [
            {"s": "BTCUSDT", "c": "45000.00", "P": "2.27"},
            {"s": "BTCUSDT", "c": "46000.00", "P": "2.50"},
            {"s": "BTCUSDT", "c": "47000.00", "P": "3.00"},
        ]
        
        result = processor.process_multiple(data_list)
        
        assert result["total"] == 3
        assert result["success"] == 3
        assert result["failed"] == 0

    def test_get_snapshot(self):
        """Test getting snapshot."""
        processor = DataProcessor()
        snapshot = processor.get_snapshot()
        
        assert snapshot is processor.price_service.snapshot

    def test_get_price(self):
        """Test getting current price."""
        processor = DataProcessor()
        assert processor.get_price() is None

    def test_is_initialized(self):
        """Test checking if processor is initialized."""
        processor = DataProcessor()
        assert processor.is_initialized() is False

    def test_reset(self):
        """Test resetting processor state."""
        processor = DataProcessor()
        processor.reset()
        
        assert processor.price_service.price_7d_reference is None