"""Price response schema for API endpoints"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PriceResponse(BaseModel):
    """
    BTC price response model.

    Used for the /api/v1/btc/price endpoint.
    """

    current_price: Optional[float] = None
    change_24h: Optional[float] = None
    change_24h_percent: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    change_7d: Optional[float] = None
    change_7d_percent: Optional[float] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }