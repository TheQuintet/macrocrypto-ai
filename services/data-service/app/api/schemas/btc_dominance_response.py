"""
Response schema for BTC dominance.
"""

from datetime import datetime

from pydantic import BaseModel


class BTCDominanceResponse(BaseModel):
    btc_dominance: float
    time: datetime
    source: str