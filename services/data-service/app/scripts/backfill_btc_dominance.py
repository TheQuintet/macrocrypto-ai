import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from app.collectors.bgeometrics import BGeometricsCollector
from app.database.btc_dominance_repository import BTCDominanceRepository
from app.database.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    collector = BGeometricsCollector()
    db = SessionLocal()

    try:
        logger.info("Fetching Bitcoin dominance history...")

        data = await collector.get_btc_dominance_history()

        logger.info("Received %d records", len(data))

        records: list[dict[str, Any]] = []

        for item in data:
            timestamp = item.get("unixTs")
            dominance = item.get("bitcoinDominance")

            if timestamp is None or dominance is None:
                continue

            records.append(
                {
                    "time": datetime.fromtimestamp(
                        int(timestamp),
                        tz=timezone.utc,
                    ),
                    "dominance": float(dominance),
                }
            )

        if not records:
            logger.warning("No valid BTC dominance records found.")
            return

        records.sort(key=lambda record: record["time"])

        repository = BTCDominanceRepository(db)

        inserted = repository.save_historical_dominance(
            records,
            source="bgeometrics_backfill",
        )

        logger.info(
            "BTC dominance backfill complete: "
            "received=%d valid=%d inserted=%d",
            len(data),
            len(records),
            inserted,
        )

        logger.info(
            "Backfill range: %s -> %s",
            records[0]["time"],
            records[-1]["time"],
        )

    except Exception:
        logger.exception("BTC dominance backfill failed")
        raise

    finally:
        db.close()
        await collector.close()


if __name__ == "__main__":
    asyncio.run(main())