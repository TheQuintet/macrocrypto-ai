import asyncio
import logging
from datetime import datetime, timezone

from app.collectors.yahoo_finance import YahooFinanceCollector
from app.database.macro_indicator_repository import MacroIndicatorRepository
from app.database.session import SessionLocal


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    collector = YahooFinanceCollector()
    db = SessionLocal()

    try:
        logger.info("Fetching 5 years of gold history...")

        records = await collector.get_gold_spot_history(
            symbol="GC=F",
            range_="5y",
            interval="1d",
        )

        logger.info("Received %d gold records", len(records))

        indicators = []

        for record in records:
            indicators.append(
                {
                    "indicator_name": "gold_spot",
                    "time": datetime.fromtimestamp(
                        record["timestamp"],
                        tz=timezone.utc,
                    ),
                    "value": float(record["price"]),
                    "previous_value": None,
                    "change_percent": None,
                    "source": "yahoo_finance",
                }
            )

        if not indicators:
            logger.warning("No valid gold records found.")
            return

        indicators.sort(key=lambda x: x["time"])

        repository = MacroIndicatorRepository(db)

        repository.create_many(indicators)

        logger.info(
            "Gold backfill complete: %d records processed",
            len(indicators),
        )

        logger.info(
            "Backfill range: %s -> %s",
            indicators[0]["time"],
            indicators[-1]["time"],
        )

    except Exception:
        logger.exception("Gold backfill failed")
        raise

    finally:
        db.close()
        await collector.close()


if __name__ == "__main__":
    asyncio.run(main())