import asyncio
import logging

from app.collectors.blockchain import BlockchainCollector
from app.database.macro_indicator_repository import MacroIndicatorRepository
from app.database.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INDICATOR_NAME = "active_addresses"


async def main() -> None:
    collector = BlockchainCollector()
    db = SessionLocal()

    try:
        logger.info("Fetching all historical active-address data...")

        records = await collector.get_active_addresses(
            timespan="all",
        )

        logger.info(
            "Received %d records from Blockchain.com",
            len(records),
        )

        if not records:
            logger.warning("No active-address records returned.")
            return

        # Process chronologically so previous_value and
        # change_percent are calculated correctly.
        records.sort(key=lambda record: record["time"])

        indicators = []

        for index, record in enumerate(records):
            current_value = float(record["value"])

            previous_value = None
            change_percent = None

            if index > 0:
                previous_value = float(records[index - 1]["value"])

                if previous_value != 0:
                    change_percent = (
                        (current_value - previous_value)
                        / previous_value
                    ) * 100

            indicators.append(
                {
                    "indicator_name": INDICATOR_NAME,
                    "time": record["time"],
                    "value": current_value,
                    "previous_value": previous_value,
                    "change_percent": (
                        round(change_percent, 4)
                        if change_percent is not None
                        else None
                    ),
                    "source": "blockchain.com",
                }
            )

        repository = MacroIndicatorRepository(db)

        logger.info(
            "Writing %d historical records to macro_indicators...",
            len(indicators),
        )

        repository.create_many(indicators)

        logger.info("Active-address historical backfill completed.")

        logger.info(
            "Backfill range: %s -> %s",
            indicators[0]["time"],
            indicators[-1]["time"],
        )

    except Exception:
        logger.exception("Active-address backfill failed")
        raise

    finally:
        db.close()
        await collector.close()


if __name__ == "__main__":
    asyncio.run(main())