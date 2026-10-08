"""Price response schema for API endpoints"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, Optional
from datetime import datetime

TimeRange = Literal["24h", "7d", "30d", "90d", "1y", "5y"]
ChartInterval = Literal["1m", "5m", "1h", "1d", "1w", "1y"]


class PriceResponse(BaseModel):
    """
    BTC price response model.

    Used for the /api/v1/btc/price endpoint.
    """
    model_config = ConfigDict( from_attributes=True, json_encoders={ datetime: lambda v: v.isoformat() if v else None }, )
    current_price: Optional[float] = None
    change_24h: Optional[float] = None
    change_24h_percent: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    change_7d: Optional[float] = None
    change_7d_percent: Optional[float] = None
    updated_at: Optional[datetime] = None


class BtcPriceHistoryPoint(BaseModel):
    """One OHLC candle. Matches frontend `BtcPriceHistoryPoint`."""

    timestamp: str
    open: float
    high: float
    low: float
    close: float


class BtcPriceHistoryResponse(BaseModel):
    """
    Historical BTC candles for the price chart.

    Matches frontend `BtcPriceHistoryResponse`.
    """

    range: TimeRange
    interval: ChartInterval
    points: list[BtcPriceHistoryPoint] = Field(default_factory=list)

    # class Config:
    #     from_attributes = True
    #     json_encoders = {
    #         datetime: lambda v: v.isoformat() if v else None
    #     }