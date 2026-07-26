"""Price service for managing BTC price state and market calculations"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.models.price_snapshot import PriceSnapshot  # ✅ CHANGED
from app.config import settings

# Setup logging
logger = logging.getLogger(__name__)


class PriceService:
    """
    Maintains BTC price state and performs market calculations.

    Responsibilities:
    - Store latest BTC price data
    - Calculate 7-day price changes
    - Provide current market snapshot
    - Initialize from historical data
    """

    def __init__(self):
        """Initialize the price service with empty state"""
        self.snapshot = PriceSnapshot(
            updated_at=datetime.now(timezone.utc)
        )

        # Reference BTC closing price from historical candles
        # Used for 7-day calculation
        self.price_7d_reference: Optional[float] = None

        logger.info("PriceService initialized")

    def initialize_from_history(self, candles: List[Dict[str, Any]]):
        """
        Initialize historical reference data.

        The first candle close price is used as
        the 7-day comparison baseline.

        Args:
            candles: List of candle data from Binance or database
                    Each candle should have 'close_price' or 'close' field
        """
        try:
            if not candles:
                logger.warning("No historical candles available")
                return

            # Handle both dict and object formats
            first_candle = candles[0]

            if isinstance(first_candle, dict):
                reference_price = first_candle.get('close_price') or first_candle.get('close')
            else:
                reference_price = getattr(first_candle, 'close_price', None) or getattr(first_candle, 'close', None)

            if reference_price is None:
                logger.warning("Could not extract close price from candle data")
                return

            self.price_7d_reference = float(reference_price)

            logger.info(f"7-day reference initialized: {self.price_7d_reference}")

            # Set initial snapshot price from latest candle
            if candles:
                last_candle = candles[-1]
                if isinstance(last_candle, dict):
                    latest_price = last_candle.get('close_price') or last_candle.get('close')
                else:
                    latest_price = getattr(last_candle, 'close_price', None) or getattr(last_candle, 'close', None)

                if latest_price:
                    self.snapshot.current_price = float(latest_price)
                    self.snapshot.updated_at = datetime.now(timezone.utc)
                    logger.info(f"Initial price set from latest candle: {self.snapshot.current_price}")

        except Exception as error:
            logger.error(f"Historical initialization failed: {error}")

    def update_price(self, price_data: Dict[str, Any]):
        """
        Update BTC price data from WebSocket or REST API.

        This is the main entry point for price updates.

        Args:
            price_data: Dictionary containing price data
                       Expected keys: price, open, high, low, volume, change_24h, etc.
        """
        try:
            # Extract price (required)
            current_price = price_data.get('price', 0.0)
            if not current_price:
                logger.warning("No price data provided")
                return

            # Extract 24h data (with fallbacks)
            change_24h = price_data.get('change_abs', price_data.get('change_24h', 0.0))
            change_24h_percent = price_data.get('change_24h', 0.0)
            high_24h = price_data.get('high', 0.0)
            low_24h = price_data.get('low', 0.0)
            volume_24h = price_data.get('volume', 0.0)

            # Update snapshot
            self.snapshot.current_price = float(current_price)
            self.snapshot.change_24h = float(change_24h)
            self.snapshot.change_24h_percent = float(change_24h_percent)
            self.snapshot.high_24h = float(high_24h)
            self.snapshot.low_24h = float(low_24h)
            self.snapshot.volume_24h = float(volume_24h)

            # Recalculate 7-day movement
            self._calculate_7d_change()

            self.snapshot.updated_at = datetime.now(timezone.utc)

            logger.debug(f"Price updated: ${current_price}")

        except Exception as error:
            logger.error(f"Price update failed: {error}")

    def update_market_data(
        self,
        current_price: float,
        change_24h: float,
        change_24h_percent: float,
        high_24h: float,
        low_24h: float,
        volume_24h: float
    ):
        """
        Update BTC market data from live WebSocket events.

        Called every time Binance sends a ticker update.

        This is a convenience method that calls update_price() with a dict.

        Args:
            current_price: Current BTC price
            change_24h: 24-hour absolute change
            change_24h_percent: 24-hour percentage change
            high_24h: 24-hour high
            low_24h: 24-hour low
            volume_24h: 24-hour volume
        """
        price_data = {
            'price': current_price,
            'change_abs': change_24h,
            'change_24h': change_24h_percent,
            'high': high_24h,
            'low': low_24h,
            'volume': volume_24h,
            'source': 'binance_ws'
        }
        self.update_price(price_data)

    def _calculate_7d_change(self):
        """Calculate absolute and percentage BTC price movement over 7 days."""
        try:
            if self.price_7d_reference is None:
                self.snapshot.change_7d = None
                self.snapshot.change_7d_percent = None
                return

            current_price = self.snapshot.current_price

            if current_price is None:
                self.snapshot.change_7d = None
                self.snapshot.change_7d_percent = None
                return

            # Calculate absolute change
            self.snapshot.change_7d = current_price - self.price_7d_reference

            # Calculate percentage change
            if self.price_7d_reference != 0:
                self.snapshot.change_7d_percent = (self.snapshot.change_7d / self.price_7d_reference) * 100
            else:
                self.snapshot.change_7d_percent = 0.0

        except Exception as error:
            logger.error(f"7-day calculation failed: {error}")

    def get_snapshot(self) -> PriceSnapshot:
        """Return current BTC market snapshot."""
        return self.snapshot

    def get_price(self) -> Optional[float]:
        """Get current BTC price."""
        return self.snapshot.current_price

    def get_7d_change(self) -> Optional[float]:
        """Get 7-day price change percentage."""
        return self.snapshot.change_7d_percent

    def get_7d_reference(self) -> Optional[float]:
        """Get the 7-day reference price."""
        return self.price_7d_reference

    def is_initialized(self) -> bool:
        """Check if price service has valid data."""
        return self.snapshot.is_valid() and self.price_7d_reference is not None

    def reset(self):
        """Reset the price service to initial state (useful for testing)."""
        self.snapshot = PriceSnapshot(updated_at=datetime.now(timezone.utc))
        self.price_7d_reference = None
        logger.info("PriceService reset")