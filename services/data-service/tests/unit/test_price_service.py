"""
Unit tests for PriceService.
"""

import pytest
from datetime import datetime, timezone
from app.services.price_service import PriceService


class TestPriceService:
    """Test suite for PriceService."""

    def test_initialization(self):
        """Test PriceService initialization."""
        service = PriceService()
        
        assert service.snapshot.current_price is None
        assert service.price_7d_reference is None
        assert service.snapshot.updated_at is not None

    def test_initialize_from_history(self):
        """Test initializing from historical candles."""
        service = PriceService()
        
        candles = [
            {"close_price": 42000.0},
            {"close_price": 43000.0},
            {"close_price": 44000.0},
            {"close_price": 45000.0},
            {"close_price": 46000.0},
            {"close_price": 47000.0},
            {"close_price": 48000.0},
            {"close_price": 49000.0},
        ]
        
        service.initialize_from_history(candles)
        
        assert service.price_7d_reference == 42000.0
        assert service.snapshot.current_price == 49000.0

    def test_initialize_from_history_empty(self):
        """Test initializing with empty candle list."""
        service = PriceService()
        service.initialize_from_history([])
        
        assert service.price_7d_reference is None

    def test_update_price(self):
        """Test updating price data."""
        service = PriceService()
        
        # Initialize with history first
        candles = [{"close_price": 42000.0}, {"close_price": 49000.0}]
        service.initialize_from_history(candles)
        
        price_data = {
            "price": 50000.0,
            "change_abs": 1000.0,
            "change_24h": 2.0,
            "high": 51000.0,
            "low": 49000.0,
            "volume": 1500.0,
        }
        
        service.update_price(price_data)
        
        assert service.snapshot.current_price == 50000.0
        assert service.snapshot.change_24h == 1000.0
        assert service.snapshot.change_24h_percent == 2.0
        assert service.snapshot.high_24h == 51000.0
        assert service.snapshot.low_24h == 49000.0
        assert service.snapshot.volume_24h == 1500.0

    def test_update_price_missing_fields(self):
        """Test updating price with missing fields."""
        service = PriceService()
        price_data = {"price": 50000.0}
        
        service.update_price(price_data)
        
        assert service.snapshot.current_price == 50000.0
        assert service.snapshot.change_24h == 0.0

    def test_update_price_no_price(self):
        """Test updating price with no price data."""
        service = PriceService()
        price_data = {}
        
        service.update_price(price_data)
        
        assert service.snapshot.current_price is None

    def test_calculate_7d_change(self):
        """Test 7-day price change calculation."""
        service = PriceService()
        
        candles = [
            {"close_price": 42000.0},
            {"close_price": 49000.0},
        ]
        service.initialize_from_history(candles)
        
        service.update_price({"price": 49000.0})
        
        # 49000 - 42000 = 7000, (7000 / 42000) * 100 = 16.67%
        expected_change_7d = 7000.0
        expected_change_7d_percent = (7000.0 / 42000.0) * 100
        
        assert service.snapshot.change_7d == expected_change_7d
        assert service.snapshot.change_7d_percent == expected_change_7d_percent

    def test_calculate_7d_change_no_reference(self):
        """Test 7-day change with no reference price."""
        service = PriceService()
        service.update_price({"price": 50000.0})
        
        assert service.snapshot.change_7d is None
        assert service.snapshot.change_7d_percent is None

    def test_get_snapshot(self):
        """Test getting snapshot."""
        service = PriceService()
        snapshot = service.get_snapshot()
        
        assert snapshot is service.snapshot

    def test_get_price(self):
        """Test getting current price."""
        service = PriceService()
        assert service.get_price() is None
        
        service.update_price({"price": 50000.0})
        assert service.get_price() == 50000.0

    def test_get_7d_change(self):
        """Test getting 7-day change."""
        service = PriceService()
        assert service.get_7d_change() is None

    def test_get_7d_reference(self):
        """Test getting 7-day reference price."""
        service = PriceService()
        assert service.get_7d_reference() is None
        
        candles = [{"close_price": 42000.0}]
        service.initialize_from_history(candles)
        assert service.get_7d_reference() == 42000.0

    def test_is_initialized(self):
        """Test checking if service is initialized."""
        service = PriceService()
        assert service.is_initialized() is False
        
        candles = [{"close_price": 42000.0}]
        service.initialize_from_history(candles)
        assert service.is_initialized() is True

    def test_reset(self):
        """Test resetting service state."""
        service = PriceService()
        candles = [{"close_price": 42000.0}]
        service.initialize_from_history(candles)
        service.update_price({"price": 50000.0})
        
        assert service.get_price() == 50000.0
        assert service.get_7d_reference() == 42000.0
        
        service.reset()
        
        assert service.get_price() is None
        assert service.get_7d_reference() is None