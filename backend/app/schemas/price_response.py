from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PriceResponse(BaseModel):
    """
    API response model for the current BTC market data.
    This model is used to serialize the data returned by the BTC price endpoint.
    """

    current_price: Optional[float] = None

    # 24-hour statistics
    change_24h: Optional[float] = None
    change_24h_percent: Optional[float] = None

    high_24h: Optional[float] = None
    low_24h: Optional[float] = None

    volume_24h: Optional[float] = None

    # 7-day statistics
    change_7d: Optional[float] = None
    change_7d_percent: Optional[float] = None

    updated_at: Optional[datetime] = None