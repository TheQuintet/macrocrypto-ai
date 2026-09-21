"""
Repository for Bitcoin market dominance data.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from logging import getLogger

from app.models.btc_dominance import BTCDominance


logger = getLogger(__name__)


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

    def save_historical_dominance(
        self,
        records: list[dict[str, Any]],
        source: str = "coinranking_backfill",
    ) -> int:
        """Bulk insert historical BTC dominance records.

        Existing timestamps are ignored so the backfill can be
        safely re-run.
        """
        if not records:
            return 0

        values = [
            {
                "time": record["time"],
                "dominance": float(record["dominance"]),
                "source": source,
            }
            for record in records
        ]

        stmt = (
            insert(BTCDominance)
            .values(values)
            .on_conflict_do_nothing(
                constraint="uq_btc_dominance_time"
            )
        )

        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount or 0

        except Exception:
            self.db.rollback()
            logger.exception("Failed to save historical BTC dominance")
            raise