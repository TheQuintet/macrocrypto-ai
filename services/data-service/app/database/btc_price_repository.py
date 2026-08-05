"""
Repository for storing historical BTC prices.
"""

from datetime import datetime, timezone

from app.database.session import SessionLocal
from app.models.btc_price import BTCPrice


class BTCPriceRepository:
    """
    Handles persistence of BTC price history both from binance WebSocket and CoinGecko API.
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