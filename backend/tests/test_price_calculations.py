"""
Unit tests for BTC price calculation logic.

Tests:
- 24h change calculation
- 7d change calculation
- High/low tracking
- Volume tracking
- Edge cases
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from app.services.price_service import PriceService, PriceSnapshot


class TestPriceCalculations:
    """Test price calculation logic."""

    def test_24h_change_calculation(self):
        """Test that 24h price change is calculated correctly."""
        # Arrange: Create service and update with test data
        service = PriceService()

        current_price = 65000.0
        change_24h = 3000.0
        change_24h_percent = 4.84
        high_24h = 66500.0
        low_24h = 61500.0
        volume_24h = 1250000000.0

        # Act: Update market data
        service.update_market_data(
            current_price=current_price,
            change_24h=change_24h,
            change_24h_percent=change_24h_percent,
            high_24h=high_24h,
            low_24h=low_24h,
            volume_24h=volume_24h,
        )

        # Assert: Verify values are stored correctly
        snapshot = service.get_snapshot()
        assert snapshot.current_price == 65000.0
        assert snapshot.change_24h == 3000.0
        assert round(snapshot.change_24h_percent, 2) == 4.84

    def test_7d_change_calculation_with_reference(self):
        """Test that 7d change is calculated correctly when reference exists."""
        # Arrange: Create service and set 7d reference
        service = PriceService()

        # Set 7d reference price (price 7 days ago)
        mock_candle = Mock()
        mock_candle.close = 58000.0
        service.initialize_from_history([mock_candle])

        # Update with current price
        service.update_market_data(
            current_price=65000.0,
            change_24h=3000.0,
            change_24h_percent=4.84,
            high_24h=66500.0,
            low_24h=61500.0,
            volume_24h=1250000000.0,
        )

        # Act: Get snapshot
        snapshot = service.get_snapshot()

        # Assert: 7d change calculated correctly
        # Expected: $65,000 - $58,000 = $7,000, 7000/58000*100 = 12.07%
        assert snapshot.change_7d == 7000.0
        assert round(snapshot.change_7d_percent, 2) == 12.07

    def test_7d_change_without_reference(self):
        """Test that 7d change returns None when no reference exists."""
        # Arrange: Create service without historical reference
        service = PriceService()

        # Update with current price (no 7d reference set)
        service.update_market_data(
            current_price=65000.0,
            change_24h=3000.0,
            change_24h_percent=4.84,
            high_24h=66500.0,
            low_24h=61500.0,
            volume_24h=1250000000.0,
        )

        # Act: Get snapshot
        snapshot = service.get_snapshot()

        # Assert: 7d change should be None
        assert snapshot.change_7d is None
        assert snapshot.change_7d_percent is None

    def test_24h_high_low_tracking(self):
        """Test that 24h high and low prices are tracked correctly."""
        # Arrange: Create service with test data
        service = PriceService()

        high_24h = 66500.0
        low_24h = 61500.0

        # Act: Update with high/low values
        service.update_market_data(
            current_price=65000.0,
            change_24h=3000.0,
            change_24h_percent=4.84,
            high_24h=high_24h,
            low_24h=low_24h,
            volume_24h=1250000000.0,
        )

        # Assert: Verify high/low are stored
        snapshot = service.get_snapshot()
        assert snapshot.high_24h == 66500.0
        assert snapshot.low_24h == 61500.0

    def test_volume_tracking(self):
        """Test that 24h volume is tracked correctly."""
        # Arrange: Create service with test data
        service = PriceService()
        volume_24h = 1250000000.0

        # Act: Update with volume
        service.update_market_data(
            current_price=65000.0,
            change_24h=3000.0,
            change_24h_percent=4.84,
            high_24h=66500.0,
            low_24h=61500.0,
            volume_24h=volume_24h,
        )

        # Assert: Verify volume is stored
        snapshot = service.get_snapshot()
        assert snapshot.volume_24h == 1250000000.0

    def test_negative_change_calculation(self):
        """Test calculation when price goes down."""
        # Arrange: Create service with test data (price decreased)
        service = PriceService()

        # Act: Update with negative change
        service.update_market_data(
            current_price=60000.0,
            change_24h=-5000.0,
            change_24h_percent=-7.69,
            high_24h=66500.0,
            low_24h=60000.0,
            volume_24h=1250000000.0,
        )

        # Assert: Verify negative values are stored
        snapshot = service.get_snapshot()
        assert snapshot.current_price == 60000.0
        assert snapshot.change_24h == -5000.0
        assert round(snapshot.change_24h_percent, 2) == -7.69

    def test_multiple_updates(self):
        """Test that multiple updates work correctly."""
        # Arrange: Create service
        service = PriceService()

        # Act: First update
        service.update_market_data(
            current_price=65000.0,
            change_24h=3000.0,
            change_24h_percent=4.84,
            high_24h=66500.0,
            low_24h=61500.0,
            volume_24h=1250000000.0,
        )

        # Act: Second update with new values
        service.update_market_data(
            current_price=66000.0,
            change_24h=4000.0,
            change_24h_percent=6.45,
            high_24h=67000.0,
            low_24h=61000.0,
            volume_24h=1300000000.0,
        )

        # Assert: Latest values are stored
        snapshot = service.get_snapshot()
        assert snapshot.current_price == 66000.0
        assert snapshot.change_24h == 4000.0
        assert round(snapshot.change_24h_percent, 2) == 6.45
        assert snapshot.high_24h == 67000.0
        assert snapshot.low_24h == 61000.0


class TestPriceServiceInitialization:
    """Test PriceService initialization and setup."""

    def test_initial_state(self):
        """Test that PriceService has correct initial state."""
        # Arrange & Act: Create service
        service = PriceService()

        # Assert: Initial state
        snapshot = service.get_snapshot()
        assert snapshot.current_price == 0
        assert snapshot.change_24h == 0
        assert snapshot.change_24h_percent == 0
        assert snapshot.high_24h == 0
        assert snapshot.low_24h == 0
        assert snapshot.volume_24h == 0
        assert snapshot.change_7d is None
        assert snapshot.change_7d_percent is None
        assert snapshot.updated_at is not None

    def test_initialize_from_history(self):
        """Test that historical initialization works."""
        # Arrange: Create service and mock candles
        service = PriceService()

        mock_candle = Mock()
        mock_candle.close = 58000.0

        # Act: Initialize from history
        service.initialize_from_history([mock_candle])

        # Assert: 7d reference is set
        assert service.price_7d_reference == 58000.0

    def test_initialize_from_history_empty(self):
        """Test that empty history is handled gracefully."""
        # Arrange: Create service
        service = PriceService()

        # Act: Initialize with empty list
        service.initialize_from_history([])

        # Assert: 7d reference remains None
        assert service.price_7d_reference is None

    def test_initialize_from_history_error(self):
        """Test that errors in history initialization are handled."""
        # Arrange: Create service
        service = PriceService()

        # Act: Initialize with invalid data
        service.initialize_from_history(None)

        # Assert: 7d reference remains None
        assert service.price_7d_reference is None


class TestEdgeCases:
    """Test edge cases for price calculations."""

    def test_zero_current_price(self):
        """Test handling when current price is zero."""
        # Arrange: Create service
        service = PriceService()

        # Act: Update with zero current price
        service.update_market_data(
            current_price=0.0,
            change_24h=0.0,
            change_24h_percent=0.0,
            high_24h=0.0,
            low_24h=0.0,
            volume_24h=0.0,
        )

        # Assert: Should handle gracefully
        snapshot = service.get_snapshot()
        assert snapshot.current_price == 0.0

    def test_large_numbers_handling(self):
        """Test handling of very large numbers."""
        # Arrange: Create service
        service = PriceService()

        # Act: Update with very large values
        service.update_market_data(
            current_price=1e12,  # $1 trillion
            change_24h=5e10,
            change_24h_percent=5.26,
            high_24h=1.1e12,
            low_24h=9.5e11,
            volume_24h=1e15,
        )

        # Assert: Should handle large numbers correctly
        snapshot = service.get_snapshot()
        assert snapshot.current_price == 1e12
        assert snapshot.change_24h == 5e10
        assert snapshot.high_24h == 1.1e12

    def test_updated_at_timestamp(self):
        """Test that updated_at timestamp is set correctly."""
        # Arrange: Create service
        service = PriceService()

        # Use naive datetime (matches what PriceService uses with utcnow())
        before_update = datetime.utcnow()

        # Act: Update
        service.update_market_data(
            current_price=65000.0,
            change_24h=3000.0,
            change_24h_percent=4.84,
            high_24h=66500.0,
            low_24h=61500.0,
            volume_24h=1250000000.0,
        )

        after_update = datetime.utcnow()

        # Assert: Timestamp is set and within range
        snapshot = service.get_snapshot()
        assert snapshot.updated_at is not None
        assert before_update <= snapshot.updated_at <= after_update


class TestPriceSnapshot:
    """Test PriceSnapshot dataclass."""

    def test_price_snapshot_creation(self):
        """Test that PriceSnapshot can be created with all fields."""
        # Arrange & Act: Create snapshot
        now = datetime.utcnow()
        snapshot = PriceSnapshot(
            current_price=65000.0,
            change_24h=3000.0,
            change_24h_percent=4.84,
            high_24h=66500.0,
            low_24h=61500.0,
            volume_24h=1250000000.0,
            change_7d=7000.0,
            change_7d_percent=12.07,
            updated_at=now,
        )

        # Assert: All fields are set correctly
        assert snapshot.current_price == 65000.0
        assert snapshot.change_24h == 3000.0
        assert snapshot.change_24h_percent == 4.84
        assert snapshot.high_24h == 66500.0
        assert snapshot.low_24h == 61500.0
        assert snapshot.volume_24h == 1250000000.0
        assert snapshot.change_7d == 7000.0
        assert snapshot.change_7d_percent == 12.07
        assert snapshot.updated_at == now

    def test_price_snapshot_optional_fields(self):
        """Test that PriceSnapshot handles optional fields correctly."""
        # Arrange & Act: Create snapshot without optional fields
        snapshot = PriceSnapshot(
            current_price=65000.0,
            change_24h=3000.0,
            change_24h_percent=4.84,
            high_24h=66500.0,
            low_24h=61500.0,
            volume_24h=1250000000.0,
        )

        # Assert: Optional fields are None
        assert snapshot.change_7d is None
        assert snapshot.change_7d_percent is None
        assert snapshot.updated_at is None