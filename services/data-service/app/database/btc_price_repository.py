"""
Repository for storing and retrieving historical BTC prices.

BTC price and volume are primarily supplied by the Binance WebSocket.
Market capitalization may be supplied by CoinGecko when available.
"""

from datetime import datetime, timedelta, timezone
from logging import getLogger

from typing import Any

from app.database.session import SessionLocal
from app.models.btc_price import BTCPrice


logger = getLogger(__name__)


class BTCPriceRepository:
    """
    Handles persistence and retrieval of historical BTC prices.

    BTC price and volume are primarily supplied by Binance.
    Market capitalization may be supplied by CoinGecko.
    """

    def save_price(
        self,
        *,
        price: float,
        volume: float,
        market_cap: float | None,
        source: str = "binance",
    ) -> None:
        """
        Store one BTC price record.
        """

        session = SessionLocal()

        try:
            record = BTCPrice(
                time=datetime.now(timezone.utc),
                price=price,
                volume=volume,
                market_cap=market_cap,
                source=source,
            )

            session.add(record)
            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    # def save_historical_prices(
    #     self,
    #     records: list[dict[str, Any]],
    #     source: str = "binance_backfill",
    # ) -> int:
    #     """Persist historical BTC candles using their original timestamps."""
    #     if not records:
    #         return 0

    #     session = SessionLocal()

    #     try:
    #         db_records = [
    #             BTCPrice(
    #                 time=record["time"],
    #                 price=float(record["price"]),
    #                 volume=(
    #                     float(record["volume"])
    #                     if record.get("volume") is not None
    #                     else None
    #                 ),
    #                 market_cap=(
    #                     float(record["market_cap"])
    #                     if record.get("market_cap") is not None
    #                     else None
    #                 ),
    #                 source=source,
    #             )
    #             for record in records
    #         ]

    #         session.add_all(db_records)
    #         session.commit()

    #         logger.info(
    #             "Persisted %d historical BTC price records",
    #             len(db_records),
    #         )

    #         return len(db_records)

    #     except Exception:
    #         session.rollback()
    #         logger.exception(
    #             "Failed to persist %d historical BTC price records",
    #             len(records),
    #         )
    #         raise

    #     finally:
    #         session.close()

    def save_historical_prices(
        self,
        records: list[dict[str, Any]],
        source: str = "binance_backfill",
    ) -> int:
        """Persist historical BTC candles using their original timestamps."""
        if not records:
            return 0

        session = SessionLocal()

        try:
            existing_times = {
                row[0]
                for row in (
                    session.query(BTCPrice.time)
                    .filter(
                        BTCPrice.time.in_(
                            record["time"] for record in records
                        )
                    )
                    .all()
                )
            }

            new_records = [
                record
                for record in records
                if record["time"] not in existing_times
            ]

            if not new_records:
                logger.info(
                    "All %d historical BTC price records already exist; "
                    "nothing to insert",
                    len(records),
                )
                return 0

            db_records = [
                BTCPrice(
                    time=record["time"],
                    price=float(record["price"]),
                    volume=(
                        float(record["volume"])
                        if record.get("volume") is not None
                        else None
                    ),
                    market_cap=(
                        float(record["market_cap"])
                        if record.get("market_cap") is not None
                        else None
                    ),
                    source=source,
                )
                for record in new_records
            ]

            session.add_all(db_records)
            session.commit()

            logger.info(
                "Persisted %d historical BTC price records",
                len(db_records),
            )

            return len(db_records)

        except Exception:
            session.rollback()
            logger.exception(
                "Failed to persist %d historical BTC price records",
                len(records),
            )
            raise

        finally:
            session.close()

    def get_history(
        self,
        *,
        days: int,
    ) -> list[BTCPrice]:
        """
        Retrieve BTC price history for the requested number of days.

        Args:
            days: Number of days of historical data.

        Returns:
            BTCPrice records ordered chronologically from
            oldest to newest.
        """

        session = SessionLocal()

        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=days)

            return (
                session.query(BTCPrice)
                .filter(
                    BTCPrice.time >= start_time,
                    BTCPrice.time <= end_time,
                )
                .order_by(BTCPrice.time.asc())
                .all()
            )

        finally:
            session.close()