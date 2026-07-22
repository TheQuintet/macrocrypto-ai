from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PriceSnapshot:
    """
    Represents the current BTC market state.

    This object stores the latest calculated market values
    received from the Binance WebSocket stream.

    It is used as the shared state object between:
    - MarketDataService
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