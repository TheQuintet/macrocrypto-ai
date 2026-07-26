"""
Unit tests for PriceSnapshot model.
"""

import pytest
from datetime import datetime, timezone
from app.models.price_snapshot import PriceSnapshot


class TestPriceSnapshot:
    """Test suite for PriceSnapshot model."""

    def test_create_empty_snapshot(self):
        """Test creating an empty price snapshot."""
        snapshot = PriceSnapshot()
        
        assert snapshot.current_price is None
        assert snapshot.change_24h is None
        assert snapshot.change_24h_percent is None
        assert snapshot.high_24h is None
        assert snapshot.low_24h is None
        assert snapshot.volume_24h is None
        assert snapshot.change_7d is None
        assert snapshot.change_7d_percent is None
        assert snapshot.updated_at is None

    def test_create_snapshot_with_values(self):
        """Test creating a price snapshot with values."""
        now = datetime.now(timezone.utc)
        
        snapshot = PriceSnapshot(
            current_price=45000.0,
            change_24h=1000.0,
            change_24h_percent=2.27,
            high_24h=46000.0,
            low_24h=44000.0,
            volume_24h=1000.0,
            change_7d=2000.0,
            change_7d_percent=4.65,
            updated_at=now
        )
        
        assert snapshot.current_price == 45000.0
        assert snapshot.change_24h == 1000.0
        assert snapshot.change_24h_percent == 2.27
        assert snapshot.high_24h == 46000.0
        assert snapshot.low_24h == 44000.0
        assert snapshot.volume_24h == 1000.0
        assert snapshot.change_7d == 2000.0
        assert snapshot.change_7d_percent == 4.65
        assert snapshot.updated_at == now

    def test_to_dict(self):
        """Test converting snapshot to dictionary."""
        now = datetime.now(timezone.utc)
        
        snapshot = PriceSnapshot(
            current_price=45000.0,
            change_24h=1000.0,
            change_24h_percent=2.27,
            high_24h=46000.0,
            low_24h=44000.0,
            volume_24h=1000.0,
            change_7d=2000.0,
            change_7d_percent=4.65,
            updated_at=now
        )
        
        result = snapshot.to_dict()
        
        assert result["current_price"] == 45000.0
        assert result["change_24h"] == 1000.0
        assert result["change_24h_percent"] == 2.27
        assert result["high_24h"] == 46000.0
        assert result["low_24h"] == 44000.0
        assert result["volume_24h"] == 1000.0
        assert result["change_7d"] == 2000.0
        assert result["change_7d_percent"] == 4.65
        assert result["updated_at"] == now.isoformat()

    def test_to_dict_with_none_values(self):
        """Test converting snapshot with None values to dictionary."""
        snapshot = PriceSnapshot()
        
        result = snapshot.to_dict()
        
        assert result["current_price"] is None
        assert result["change_24h"] is None
        assert result["change_24h_percent"] is None
        assert result["high_24h"] is None
        assert result["low_24h"] is None
        assert result["volume_24h"] is None
        assert result["change_7d"] is None
        assert result["change_7d_percent"] is None
        assert result["updated_at"] is None

    def test_is_valid_with_price(self):
        """Test is_valid returns True when price is valid."""
        snapshot = PriceSnapshot(current_price=45000.0)
        assert snapshot.is_valid() is True

    def test_is_valid_with_zero_price(self):
        """Test is_valid returns False when price is zero."""
        snapshot = PriceSnapshot(current_price=0.0)
        assert snapshot.is_valid() is False

    def test_is_valid_with_none_price(self):
        """Test is_valid returns False when price is None."""
        snapshot = PriceSnapshot(current_price=None)
        assert snapshot.is_valid() is False

    def test_str_representation(self):
        """Test string representation of snapshot."""
        now = datetime.now(timezone.utc)
        snapshot = PriceSnapshot(current_price=45000.0, updated_at=now)
        
        result = str(snapshot)
        assert "PriceSnapshot" in result
        assert "45000.0" in result
        assert str(now) in result