"""
Repository for Bitcoin market dominance data.
"""

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.btc_dominance import BTCDominance


class BTCDominanceRepository:
    """
    Database operations for BTC dominance.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        time: datetime,
        dominance: float,
        source: str = "coingecko",
    ) -> BTCDominance:
        record = BTCDominance(
            time=time,
            dominance=dominance,
            source=source,
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return record

    def get_latest(self) -> BTCDominance | None:
        return (
            self.db.query(BTCDominance)
            .order_by(desc(BTCDominance.time))
            .first()
        )