"""
Repository for storing and retrieving historical BTC prices.

BTC price and volume are primarily supplied by the Binance WebSocket.
Market capitalization may be supplied by CoinGecko when available.
"""

from datetime import datetime, timedelta, timezone

from app.database.session import SessionLocal
from app.models.btc_price import BTCPrice


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