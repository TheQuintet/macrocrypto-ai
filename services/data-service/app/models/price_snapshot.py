"""Price Snapshot - Current BTC market state data model"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any


@dataclass
class PriceSnapshot:
    """
    Represents the current BTC market state.

    This object stores the latest calculated market values
    received from the Binance WebSocket stream.

    It is used as the shared state object between:
    - DataProcessor
    - PriceService
    - API endpoints

    Optional fields allow the application to start before
    complete market data is available.
    """

    # Current BTC market price
    current_price: Optional[float] = None

    # ==============================
    # 24-hour market statistics
    # ==============================

    # Absolute BTC price movement over the last 24 hours
    change_24h: Optional[float] = None

    # Percentage BTC price movement over the last 24 hours
    change_24h_percent: Optional[float] = None

    # Highest BTC price recorded in the last 24 hours
    high_24h: Optional[float] = None

    # Lowest BTC price recorded in the last 24 hours
    low_24h: Optional[float] = None

    # BTC trading volume over the last 24 hours
    volume_24h: Optional[float] = None

    # ==============================
    # 7-day calculated statistics
    # ==============================

    # Absolute BTC price change compared with
    # the historical 7-day reference price
    change_7d: Optional[float] = None

    # Percentage BTC price change compared with
    # the historical 7-day reference price
    change_7d_percent: Optional[float] = None

    # Timestamp of the latest market update
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert snapshot to dictionary for API responses.
        """
        return {
            "current_price": self.current_price,
            "change_24h": self.change_24h,
            "change_24h_percent": self.change_24h_percent,
            "high_24h": self.high_24h,
            "low_24h": self.low_24h,
            "volume_24h": self.volume_24h,
            "change_7d": self.change_7d,
            "change_7d_percent": self.change_7d_percent,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def is_valid(self) -> bool:
        """
        Check if snapshot has valid price data.
        """
        return self.current_price is not None and self.current_price > 0

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"PriceSnapshot(price=${self.current_price}, updated={self.updated_at})"