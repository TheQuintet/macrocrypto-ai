"""
Scheduled background jobs.

Responsibilities:
- Trigger macro/FRED updates using MACRO_UPDATE_INTERVAL_MINUTES.
- Trigger current macroeconomic regime classification.
- Trigger BTC regime performance calculation.
- Trigger similar historical period analysis.
- Keep macro_regimes current (reconcile against current_regime
  on each daily regime run).
- Backfill historical macro_regimes on startup (if empty) and
  weekly thereafter.
- Support configurable QA execution intervals.
- Handle scheduler errors without crashing the background loop.
- Clean up database/service resources after each scheduled run.

Configuration:

MACRO_UPDATE_INTERVAL_MINUTES
    Controls the macro/FRED update scheduler.

CURRENT_REGIME_UPDATE_INTERVAL_MINUTES
    Controls the current-regime scheduler.

REGIME_PERFORMANCE_QA_MODE
    Enables regime_performance processing during QA.

Note:
    regime_event_analysis is intentionally not populated. The QA
    placeholder was removed; see RegimeEventService for details.
"""

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

from app.config import settings
from app.database.session import SessionLocal
from app.services.economic_calendar_service import EconomicCalendarService
from app.services.indicator_service import IndicatorService
from app.services.equity_corr_service import EquityCorrService
from app.services.active_addresses_service import ActiveAddressesService
from app.services.gold_spot_service import GoldSpotService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# SCHEDULE HELPERS
# ============================================================


async def wait_until_next_run(
    hour: int,
    minute: int,
    job_name: str,
):
    """
    Sleep until the next configured production UTC schedule.
    """

    now = datetime.now(timezone.utc)

    next_run = now.replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0,
    )

    if next_run <= now:
        next_run += timedelta(days=1)

    wait_seconds = (
        next_run - now
    ).total_seconds()

    logger.info(
        "Next %s scheduled at %s",
        job_name,
        next_run.isoformat(),
    )

    await asyncio.sleep(wait_seconds)


async def wait_until_next_hour(
    minute_offset: int,
    job_name: str,
):
    """
    Sleep until the next occurrence of <minute_offset> past the hour.

    Example: minute_offset=1 sleeps until the next :01.
    """
    now = datetime.now(timezone.utc)

    next_run = now.replace(
        minute=minute_offset,
        second=0,
        microsecond=0,
    )

    if next_run <= now:
        next_run += timedelta(hours=1)

    wait_seconds = (next_run - now).total_seconds()

    logger.info(
        "Next %s scheduled at %s",
        job_name,
        next_run.isoformat(),
    )

    await asyncio.sleep(wait_seconds)


async def wait_for_interval_hours(
    hours: float,
    job_name: str,
):
    """
    Sleep for a fixed interval of hours.

    Unlike wait_until_next_run and wait_until_next_hour, this
    helper is anchored to "now" rather than to a wall-clock
    boundary. Used by tasks that run on a rolling interval
    (e.g. the hourly gap scan, every 6h) rather than at a fixed
    time-of-day or minute-past-the-hour.

    hours may be fractional (e.g. 0.5 for a 30-minute interval),
    which is useful for testing.
    """
    now = datetime.now(timezone.utc)
    next_run = now + timedelta(hours=hours)

    logger.info(
        "Next %s in %.1f hours (at %s)",
        job_name,
        hours,
        next_run.isoformat(),
    )

    await asyncio.sleep(hours * 3600)


# ============================================================
# MACRO / FRED SCHEDULER
# ============================================================


async def periodic_macro_collection(cache_client=None):
    logger.info("📊 Macro/FRED scheduler started")

    if settings.MACRO_UPDATE_INTERVAL_MINUTES > 0:
        logger.info(
            "Macro QA interval mode enabled: running every %s minute(s)",
            settings.MACRO_UPDATE_INTERVAL_MINUTES,
        )
    else:
        logger.info(
            "Macro production schedule mode enabled: running daily at %02d:%02d UTC",
            settings.MACRO_UPDATE_HOUR_UTC,
            settings.MACRO_UPDATE_MINUTE_UTC,
        )

    while True:
        try:
            if settings.MACRO_UPDATE_INTERVAL_MINUTES > 0:
                await asyncio.sleep(
                    settings.MACRO_UPDATE_INTERVAL_MINUTES * 60
                )
            else:
                await wait_until_next_run(
                    settings.MACRO_UPDATE_HOUR_UTC,
                    settings.MACRO_UPDATE_MINUTE_UTC,
                    "macro/FRED update",
                )

            logger.info("📊 Macro/FRED scheduler woke up")

            db = SessionLocal()
            equity_corr_service = None
            active_addresses_service = None
            gold_spot_service = None

            try:
                service = IndicatorService(
                    db,
                    cache_client=cache_client,
                )

                result = await service.update_all_indicators()

                logger.info(
                    "📊 Macro/FRED collection result: %s",
                    result,
                )

                # ==================================================
                # DERIVED EQUITY CORRELATION
                # ==================================================

                equity_corr_service = EquityCorrService(db)

                equity_corr_records = (
                    await equity_corr_service.calculate()
                )

                if equity_corr_records:
                    equity_corr_service.repository.create_many(
                        equity_corr_records
                    )

                    logger.info(
                        "📈 equity_corr calculation completed: "
                        "%d records persisted",
                        len(equity_corr_records),
                    )
                else:
                    logger.warning(
                        "📈 equity_corr calculation produced no records"
                    )

                # Active address from blockchain.com is a derived feature that is not part of the FRED collection.
                active_addresses_service = ActiveAddressesService(db)

                active_addresses_records = (
                    await active_addresses_service.calculate()
                )

                if active_addresses_records:
                    active_addresses_service.repository.create_many(
                        active_addresses_records
                    )

                    logger.info(
                        "📈 Active addresses calculation completed: "
                        "📈 Persisted %d active_addresses records",
                        len(active_addresses_records),
                    )

                else:
                    logger.warning(
                        "📈 Active addresses calculation produced no records"
                    )

                # Gold spot from Yahoo Finance
                gold_spot_service = GoldSpotService(db)

                gold_spot_records = (
                    await gold_spot_service.collect()
                )

                if gold_spot_records:
                    gold_spot_service.repository.create_many(
                        gold_spot_records
                    )

                    logger.info(
                        "🪙 Gold spot data acquisition completed: "
                        "Persisted %d gold_spot records",
                        len(gold_spot_records),
                    )

                else:
                    logger.warning(
                        "🪙 Gold spot data acquisition produced no records"
                    )

            finally:
                if equity_corr_service:
                    await equity_corr_service.close()
                if active_addresses_service:
                    await active_addresses_service.close()
                if gold_spot_service:
                    await gold_spot_service.close()

                db.close()

            logger.info("📊 Macro/FRED scheduled job completed")

        except asyncio.CancelledError:
            logger.info("Macro/FRED scheduler cancelled")
            raise

        except Exception:
            logger.exception("🔥 Macro/FRED scheduler failed")


# ============================================================
# HIGH YIELD CREDIT STRESS PROXY SCHEDULER (Phase B, Chat 5, B5)
# ============================================================


async def periodic_high_yield_credit_stress():
    """
    Daily collection of the high_yield_credit_stress_proxy.

    Computes (HYG / SHY).pct_change() from Yahoo Finance and
    writes one row per trading day into the raw macro_indicators
    table with:
        indicator_name = 'high_yield_credit_stress_proxy'
        source         = 'derived'

    Runs once per day at HY_PROXY_UPDATE_HOUR_UTC:
    HY_PROXY_UPDATE_MINUTE_UTC (default 03:00 UTC), staggered
    after the 01:00 UTC macro/FRED task and before the 03:30 UTC
    vintages task (B6).

    Idempotent: the service returns one record per trading day
    in the HY_PROXY_LOOKBACK_DAYS window, and the repository's
    ON CONFLICT (time, indicator_name) clause skips any day
    already stored. Re-running on the same day is a no-op.

    Consumed by features_db as the
    high_yield_credit_stress_proxy column. See
    docs/data-service-schemas.md §5, row 14.
    """

    from app.services.high_yield_credit_stress_service import (
        HighYieldCreditStressService,
    )

    logger.info("📉 HY credit stress scheduler started")
    logger.info(
        "HY credit stress production schedule enabled: "
        "running daily at %02d:%02d UTC",
        settings.HY_PROXY_UPDATE_HOUR_UTC,
        settings.HY_PROXY_UPDATE_MINUTE_UTC,
    )

    while True:
        try:
            await wait_until_next_run(
                settings.HY_PROXY_UPDATE_HOUR_UTC,
                settings.HY_PROXY_UPDATE_MINUTE_UTC,
                "high yield credit stress update",
            )

            logger.info("📉 HY credit stress scheduler woke up")

            db = SessionLocal()
            service = None

            try:
                service = HighYieldCreditStressService(db)

                records = await service.collect()

                if records:
                    service.repository.create_many(records)

                    logger.info(
                        "📉 Persisted %d high_yield_credit_stress_proxy "
                        "record(s)",
                        len(records),
                    )
                else:
                    logger.warning(
                        "📉 HY credit stress calculation produced "
                        "no records"
                    )

            finally:
                if service:
                    await service.close()
                db.close()

            logger.info(
                "📉 HY credit stress scheduled job completed"
            )

        except asyncio.CancelledError:
            logger.info("HY credit stress scheduler cancelled")
            raise

        except Exception:
            logger.exception(
                "🔥 HY credit stress scheduler failed"
            )


# ============================================================
# MACRO INDICATOR VINTAGES SCHEDULER (Phase B, Chat 5, B6)
# ============================================================


async def periodic_macro_vintages():
    """
    Daily collection of FRED macro indicator vintages.

    Fetches the full revision history (vintages) for 5
    revision-prone FRED series and writes them to
    macro_indicator_vintages:

        cpi                 <- CPIAUCSL
        unemployment        <- UNRATE
        federal_funds_rate  <- FEDFUNDS
        m2_money_supply     <- M2SL
        gdp                 <- GDP

    Runs once per day at VINTAGE_UPDATE_HOUR_UTC:
    VINTAGE_UPDATE_MINUTE_UTC (default 03:30 UTC), staggered
    after the 03:00 UTC HY credit stress job (B5) and after the
    01:00 UTC macro/FRED task.

    Why vintages: FRED revisions mean the value known for an
    observation changes over time. The features writer (B4)
    needs point-in-time values to avoid look-ahead bias when
    training. See migration 008 and
    app/services/macro_vintage_service.py.

    Idempotent: the service returns one record per
    (series_id, observation_date, release_date) in the
    VINTAGE_LOOKBACK_YEARS window, and the repository's
    ON CONFLICT (series_id, observation_date, release_date)
    clause skips any triple already stored. Re-running on the
    same day is a no-op.

    Note: this task requires a real FRED_API_KEY. If the key is
    missing or still the placeholder from .env, the service
    constructor raises RuntimeError; the outer except logs it
    and the loop continues to the next scheduled run.

    Consumed by features_db for 5 of its 53 columns. See
    docs/data-service-schemas.md §5, rows 15-19.
    """

    from app.services.macro_vintage_service import (
        MacroVintageService,
    )

    logger.info("📚 Macro vintage scheduler started")
    logger.info(
        "Macro vintage production schedule enabled: "
        "running daily at %02d:%02d UTC",
        settings.VINTAGE_UPDATE_HOUR_UTC,
        settings.VINTAGE_UPDATE_MINUTE_UTC,
    )

    while True:
        try:
            await wait_until_next_run(
                settings.VINTAGE_UPDATE_HOUR_UTC,
                settings.VINTAGE_UPDATE_MINUTE_UTC,
                "macro vintage update",
            )

            logger.info("📚 Macro vintage scheduler woke up")

            db = SessionLocal()
            service = None

            try:
                service = MacroVintageService(db)

                records = await service.collect()

                if records:
                    service.repository.create_many(records)

                    logger.info(
                        "📚 Persisted %d macro vintage record(s)",
                        len(records),
                    )
                else:
                    logger.warning(
                        "📚 Macro vintage collection produced "
                        "no records"
                    )

            finally:
                if service:
                    await service.close()
                db.close()

            logger.info(
                "📚 Macro vintage scheduled job completed"
            )

        except asyncio.CancelledError:
            logger.info("Macro vintage scheduler cancelled")
            raise

        except Exception:
            logger.exception(
                "🔥 Macro vintage scheduler failed"
            )


# ============================================================
# FEATURES_DB SCHEDULER (Phase B, Chat 5, B4)
# ============================================================


async def periodic_features_db():
    """
    Hourly write of the features_db ML feature table.

    Runs at :05 of every hour, staggered after the hourly
    materializers (BTC at :01, macro at :02) so a slow upstream
    writer does not delay features_db.

    Writes the just-completed hour's feature row. Enforces the
    D9 writer lag by construction:

        target_hour = floor(now) - 1h

    At 14:05, the row written is for 13:00, whose target y is
    btc_prices_hourly.close at 14:00. The 14:00 row is not
    written (its y is 15:00's close, unknown).

    Idempotent: FeaturesDBRepository.create_many uses
    ON CONFLICT (ds) DO NOTHING. Re-running an hour is a no-op.

    The task does not raise on a "no row to write" outcome: if
    the successor hour's close has not yet landed (unusual, but
    possible if an upstream job was delayed), the writer logs
    at debug and returns False. The loop continues to the next
    scheduled run.

    See:
        migrations/009_create_features_db.sql
        app/services/feature_builder_service.py  (SSOT)
        app/services/features_db_writer.py
        docs/data-service-schemas.md §3, §5
    """

    from app.services.features_db_writer import FeaturesDBWriter

    logger.info("🧬 FeaturesDB scheduler started")
    logger.info(
        "FeaturesDB production schedule enabled: "
        "running hourly at :%02d UTC",
        settings.FEATURES_DB_UPDATE_MINUTE_UTC,
    )

    while True:
        try:
            await wait_until_next_hour(
                settings.FEATURES_DB_UPDATE_MINUTE_UTC,
                "features_db write",
            )

            logger.info("🧬 FeaturesDB scheduler woke up")

            db = SessionLocal()
            writer = None

            try:
                writer = FeaturesDBWriter(db)
                wrote = writer.write_current_hour()

                if wrote:
                    logger.info(
                        "🧬 Wrote features_db row for the "
                        "previous hour"
                    )
                else:
                    logger.info(
                        "🧬 Skipped features_db write "
                        "(no row available for the "
                        "previous hour)"
                    )

            finally:
                db.close()

            logger.info(
                "🧬 FeaturesDB scheduled job completed"
            )

        except asyncio.CancelledError:
            logger.info("FeaturesDB scheduler cancelled")
            raise

        except Exception:
            logger.exception(
                "🔥 FeaturesDB scheduler failed"
            )


# ============================================================
# ECONOMIC CALENDAR SCHEDULER
# ============================================================


async def periodic_economic_calendar_collection():
    """
    Scheduled economic calendar data collection.

    QA/development:
        MACRO_UPDATE_INTERVAL_MINUTES > 0
        runs every N minutes.

    Production:
        MACRO_UPDATE_INTERVAL_MINUTES = 0
        runs once daily at the configured UTC time.

    Responsibilities:
        - Wait for the configured schedule.
        - Fetch economic calendar events from FRED.
        - Persist new events.
        - Handle collection errors without stopping the scheduler.
        - Clean up the service and database session.
    """

    logger.info(
        "📅 Economic calendar scheduler started"
    )

    if settings.MACRO_UPDATE_INTERVAL_MINUTES > 0:

        logger.info(
            "Economic calendar QA interval mode enabled: "
            "running every %s minute(s)",
            settings.MACRO_UPDATE_INTERVAL_MINUTES,
        )

    else:

        logger.info(
            "Economic calendar production schedule enabled: "
            "running daily at %02d:%02d UTC",
            settings.MACRO_UPDATE_HOUR_UTC,
            settings.MACRO_UPDATE_MINUTE_UTC,
        )

    while True:

        try:

            # ==================================================
            # WAIT FOR NEXT EXECUTION
            # ==================================================

            if settings.MACRO_UPDATE_INTERVAL_MINUTES > 0:

                await asyncio.sleep(
                    settings.MACRO_UPDATE_INTERVAL_MINUTES
                    * 60
                )

            else:

                await wait_until_next_run(
                    settings.MACRO_UPDATE_HOUR_UTC,
                    settings.MACRO_UPDATE_MINUTE_UTC,
                    "economic calendar update",
                )

            logger.info(
                "📅 Economic calendar scheduler woke up"
            )

            # ==================================================
            # DATABASE SESSION
            # ==================================================

            db = SessionLocal()
            service = None

            try:

                service = EconomicCalendarService(db)

                logger.info(
                    "📅 Starting economic calendar collection "
                    "(lookback=%s days)",
                    settings.FRED_CALENDAR_LOOKBACK_DAYS,
                )

                events = await service.collect_events(
                    days=settings.FRED_CALENDAR_LOOKBACK_DAYS
                )

                logger.info(
                    "📅 Economic calendar collection completed: "
                    "%d new events stored",
                    len(events),
                )

            except Exception:

                logger.exception(
                    "🔥 Economic calendar collection failed"
                )

            finally:

                if service:

                    try:
                        await service.close()

                    except Exception:

                        logger.exception(
                            "⚠️ Failed to close economic "
                            "calendar service"
                        )

                try:
                    db.close()

                except Exception:

                    logger.exception(
                        "⚠️ Failed to close economic "
                        "calendar database session"
                    )

            logger.info(
                "📅 Economic calendar scheduled job completed"
            )

        except asyncio.CancelledError:

            logger.info(
                "Economic calendar scheduler cancelled"
            )

            raise

        except Exception:

            logger.exception(
                "🔥 Economic calendar scheduler failed"
            )


# ============================================================
# MACRO_REGIMES RECONCILIATION HELPER
# ============================================================


def _reconcile_macro_regime_row(db, current_regime):
    """
    Keep macro_regimes in sync with current_regime.

    The live path writes current_regime but not macro_regimes.
    This helper closes that gap: after each daily current-regime
    classification, ensure the historical table has exactly one
    open row matching the fresh label.

    Behavior:
        - No open row in macro_regimes
            -> create one starting today.
        - Open row exists with the same regime_type
            -> no-op.
        - Open row exists with a different regime_type
            -> close the open row at today, then create a new
               open row starting today.

    Idempotent: running twice in a row with the same label is a
    no-op the second time.

    Never raises: any failure is logged and swallowed so the
    surrounding daily job continues.
    """

    if current_regime is None:
        return

    from app.database.regime_repository import RegimeRepository

    try:
        repository = RegimeRepository(db)

        open_row = repository.get_current_regime()
        today = date.today()
        new_type = current_regime.regime_type

        if open_row is None:
            repository.create_regime(
                regime_type=new_type,
                start_date=today,
            )
            logger.info(
                "macro_regimes: created initial open row for %s",
                new_type,
            )
            return

        if open_row.regime_type == new_type:
            # Nothing to do.
            return

        repository.close_regime(open_row, today)
        repository.create_regime(
            regime_type=new_type,
            start_date=today,
        )
        logger.info(
            "macro_regimes: closed %s, opened %s",
            open_row.regime_type,
            new_type,
        )

    except Exception:
        logger.exception(
            "macro_regimes reconciliation failed; will retry "
            "on next daily run"
        )


# ============================================================
# CURRENT REGIME SCHEDULER
# ============================================================


async def periodic_regime_collection():
    """
    Scheduled current macroeconomic regime processing.

    QA/development:
        CURRENT_REGIME_UPDATE_INTERVAL_MINUTES > 0
        runs every N minutes.

    Production:
        CURRENT_REGIME_UPDATE_INTERVAL_MINUTES = 0
        uses the configured daily UTC schedule.

    Workflow:

    1. Wait for configured QA interval or production schedule.
    2. Process current macroeconomic regime.
    3. Reconcile macro_regimes (close/open the open row).
    4. Calculate/update BTC regime performance when enabled.
    5. Update similar historical periods.
    6. Clean up database/service resources.
    7. Continue until cancelled.
    """

    logger.info(
        "🔥 Current regime scheduler started"
    )

    # ========================================================
    # CONFIGURATION STATUS
    # ========================================================

    if settings.CURRENT_REGIME_UPDATE_INTERVAL_MINUTES > 0:

        logger.info(
            "Current regime QA interval mode enabled: "
            "running every %s minute(s)",
            settings.CURRENT_REGIME_UPDATE_INTERVAL_MINUTES,
        )

    else:

        logger.info(
            "Current regime production schedule enabled: "
            "running at %02d:%02d UTC",
            settings.CURRENT_REGIME_UPDATE_HOUR_UTC,
            settings.CURRENT_REGIME_UPDATE_MINUTE_UTC,
        )

    logger.info(
        "Regime performance QA mode: %s",
        settings.REGIME_PERFORMANCE_QA_MODE,
    )

    # ========================================================
    # IMPORTS
    # ========================================================

    from app.database.session import SessionLocal

    from app.database.regime_repository import (
        RegimeRepository,
    )

    from app.services.current_regime_service import (
        CurrentRegimeService,
    )

    from app.services.regime_performance_service import (
        RegimePerformanceService,
    )

    from app.services.similar_period_service import (
        SimilarPeriodService,
    )

    # ========================================================
    # MAIN LOOP
    # ========================================================

    while True:

        try:

            # ==================================================
            # WAIT FOR NEXT REGIME EXECUTION
            # ==================================================

            if (
                settings.CURRENT_REGIME_UPDATE_INTERVAL_MINUTES
                > 0
            ):

                await asyncio.sleep(
                    settings.CURRENT_REGIME_UPDATE_INTERVAL_MINUTES
                    * 60
                )

            else:

                await wait_until_next_run(
                    settings.CURRENT_REGIME_UPDATE_HOUR_UTC,
                    settings.CURRENT_REGIME_UPDATE_MINUTE_UTC,
                    "current regime update",
                )

            logger.info(
                "🔥 Current regime scheduler woke up"
            )

            db = SessionLocal()
            service = None

            try:

                # ==================================================
                # 1. CURRENT REGIME CLASSIFICATION
                # ==================================================

                service = CurrentRegimeService(db)

                current_regime = (
                    await service.process_current_regime()
                )

                logger.info(
                    "Current regime processing completed: %s",
                    current_regime,
                )

                # ==================================================
                # 2. RECONCILE macro_regimes
                # ==================================================
                #
                # Keep the historical table aligned with the
                # fresh current_regime snapshot. The backfill
                # filled history; this step keeps it current
                # going forward.

                _reconcile_macro_regime_row(
                    db, current_regime
                )

                # ==================================================
                # 3. REGIME PERFORMANCE
                # ==================================================

                if current_regime is not None:

                    if settings.REGIME_PERFORMANCE_QA_MODE:

                        logger.info(
                            "📈 Regime performance QA mode enabled"
                        )

                        try:
                            from app.database.regime_repository import (
                                RegimeRepository,
                            )

                            regime_repository = RegimeRepository(db)

                            # CurrentRegime is the snapshot used by the
                            # current-regime API.
                            #
                            # RegimePerformanceService requires MacroRegime
                            # because it needs start_date/end_date.
                            macro_regime = (
                                regime_repository.get_current_regime()
                            )

                            if macro_regime is None:

                                logger.warning(
                                    "⚠️ No active MacroRegime found for "
                                    "current regime performance calculation"
                                )

                            else:

                                performance_service = (
                                    RegimePerformanceService(db)
                                )

                                performance_result = (
                                    performance_service
                                    .calculate_regime_performance(
                                        macro_regime
                                    )
                                )

                                logger.info(
                                    "Regime performance calculation "
                                    "completed: %s",
                                    performance_result,
                                )

                        except Exception:

                            logger.exception(
                                "❌ Regime performance calculation failed"
                            )

                    else:

                        logger.info(
                            "Regime performance QA mode disabled; "
                            "skipping regime_performance"
                        )

                else:

                    logger.info(
                        "No current regime identified; "
                        "skipping regime_performance"
                    )

                # ==================================================
                # 4. SIMILAR HISTORICAL PERIODS
                # ==================================================

                if current_regime is not None:

                    similar_service = (
                        SimilarPeriodService(db)
                    )

                    try:

                        similar_result = (
                            similar_service.find_similar_periods()
                        )

                        logger.info(
                            "Similar historical periods update "
                            "completed: %s",
                            similar_result,
                        )

                    except Exception:

                        logger.exception(
                            "❌ Similar historical periods update failed"
                        )

                else:

                    logger.info(
                        "No current regime identified; "
                        "skipping similar historical periods"
                    )

                # ==================================================
                # COMPLETE
                # ==================================================

                logger.info(
                    "🔥 Current regime scheduled job "
                    "completed successfully"
                )

            finally:

                if service:
                    await service.close()

                db.close()

                logger.info(
                    "Current regime database session closed"
                )

        # ========================================================
        # CANCELLATION
        # ========================================================

        except asyncio.CancelledError:

            logger.info(
                "Current regime scheduler cancelled"
            )

            raise

        # ========================================================
        # UNEXPECTED ERROR
        # ========================================================

        except Exception:

            logger.exception(
                "🔥 Current regime scheduler failed"
            )


# ============================================================
# HOURLY BTC PRICES SCHEDULER (Phase B, Chat 3)
# ============================================================


async def periodic_hourly_btc_prices():
    """
    Materialize btc_prices_hourly for the previous hour.

    Runs at :01 of every hour. Writes the hour [H-1, H) where H
    is the current wall-clock hour, i.e. the just-completed hour.
    """
    from app.services.hourly_btc_prices_service import (
        HourlyBTCPricesService,
    )

    logger.info("⏱️  Hourly BTC prices scheduler started")

    while True:
        try:
            await wait_until_next_hour(1, "hourly BTC prices")

            logger.info("⏱️  Hourly BTC prices scheduler woke up")

            now = datetime.now(timezone.utc)
            target_hour = now.replace(
                minute=0, second=0, microsecond=0
            ) - timedelta(hours=1)

            db = SessionLocal()
            service = None

            try:
                service = HourlyBTCPricesService(db)
                wrote = service.write_hour(target_hour)

                if wrote:
                    logger.info(
                        "⏱️  Wrote btc_prices_hourly row for %s",
                        target_hour.isoformat(),
                    )
                else:
                    logger.info(
                        "⏱️  Skipped btc_prices_hourly %s "
                        "(no raw ticks)",
                        target_hour.isoformat(),
                    )
            finally:
                if service:
                    await service.close()
                db.close()

        except asyncio.CancelledError:
            logger.info("Hourly BTC prices scheduler cancelled")
            raise

        except Exception:
            logger.exception("🔥 Hourly BTC prices scheduler failed")


# ============================================================
# HOURLY MACRO INDICATORS SCHEDULER (Phase B, Chat 3)
# ============================================================


async def periodic_hourly_macro_indicators():
    """
    Materialize macro_indicators_hourly for the previous hour.

    Runs at :02 of every hour (one minute after the BTC hourly
    writer, so the two don't contend for the same connection).
    Writes the hour [H-1, H) where H is the current wall-clock
    hour.
    """
    from app.services.hourly_macro_indicators_service import (
        HourlyMacroIndicatorsService,
    )

    logger.info("📈 Hourly macro indicators scheduler started")

    while True:
        try:
            await wait_until_next_hour(2, "hourly macro indicators")

            logger.info("📈 Hourly macro indicators scheduler woke up")

            now = datetime.now(timezone.utc)
            target_hour = now.replace(
                minute=0, second=0, microsecond=0
            ) - timedelta(hours=1)

            db = SessionLocal()
            service = None

            try:
                service = HourlyMacroIndicatorsService(db)
                service.write_hour(target_hour)

                logger.info(
                    "📈 Wrote macro_indicators_hourly row for %s",
                    target_hour.isoformat(),
                )
            finally:
                if service:
                    await service.close()
                db.close()

        except asyncio.CancelledError:
            logger.info("Hourly macro indicators scheduler cancelled")
            raise

        except Exception:
            logger.exception(
                "🔥 Hourly macro indicators scheduler failed"
            )


# ============================================================
# HOURLY GAP SCAN SCHEDULER (Phase B, Chat 4, C4-3)
# ============================================================


def _run_gap_scan_once(prefix: str) -> None:
    """
    Run one gap scan across both hourly tables and log the result.

    Read-only. Never repairs. Never fetches from external
    providers. The point is visibility: if a writer has stopped
    producing rows, we want a warning in the logs before the next
    backfill runs.

    prefix: "startup scan" or "periodic scan", used in log lines
    so operators can distinguish the two call sites.
    """
    from app.services.gap_detection_service import (
        SUPPORTED_TABLES,
        scan as scan_gaps,
    )

    now = datetime.now(timezone.utc)
    lookback_hours = settings.HOURLY_GAP_SCAN_LOOKBACK_HOURS
    start = now - timedelta(hours=lookback_hours)

    for table in SUPPORTED_TABLES:
        try:
            report = scan_gaps(table, start, now)
        except Exception:
            logger.exception(
                "🔍 Hourly gap scan (%s) failed for %s",
                prefix,
                table,
            )
            continue

        if not report.has_gaps:
            logger.info(
                "🔍 Hourly gap scan (%s): %s has no gaps "
                "over the last %dh",
                prefix,
                table,
                lookback_hours,
            )
            continue

        logger.warning(
            "🔍 Hourly gap scan (%s): %s has %d missing hour(s) "
            "over the last %dh "
            "(MATERIALIZATION_GAP=%d, RAW_DATA_GAP=%d). "
            "Run `python -m app.scripts.verify_hourly_tables "
            "--table %s --days %d` for details, or --repair "
            "to fix MATERIALIZATION_GAP hours.",
            prefix,
            table,
            report.missing_count,
            lookback_hours,
            report.materialization_count,
            report.raw_data_count,
            "btc" if table == "btc_prices_hourly" else "macro",
            max(1, lookback_hours // 24),
        )

        # Show the first few missing hours for quick triage.
        for item in report.first_missing(5):
            logger.warning(
                "🔍   %s  %s",
                item.hour.isoformat(),
                item.classification.value,
            )


async def periodic_hourly_gap_scan():
    """
    Periodic read-only scan of the hourly tables for gaps.

    Chat 4 C4-3: visibility only. Never repairs, never fetches
    from external providers. If gaps exist, emits a WARNING with
    a pointer to verify_hourly_tables.

    Runs once at startup (wrapped in its own try/except so a
    failed startup scan does not prevent the interval loop from
    starting), then every HOURLY_GAP_SCAN_INTERVAL_HOURS.

    Controlled by HOURLY_GAP_SCAN_ENABLED. If disabled, this
    task should not be started at all by main.py, but as a
    defensive measure it also self-disables if called.
    """
    if not settings.HOURLY_GAP_SCAN_ENABLED:
        logger.info(
            "🔍 Hourly gap scan disabled "
            "(HOURLY_GAP_SCAN_ENABLED=False); scheduler exiting"
        )
        return

    logger.info(
        "🔍 Hourly gap scan scheduler started "
        "(interval=%sh, lookback=%sh)",
        settings.HOURLY_GAP_SCAN_INTERVAL_HOURS,
        settings.HOURLY_GAP_SCAN_LOOKBACK_HOURS,
    )

    # Startup scan: run once immediately, then enter the interval
    # loop. Wrapped so a failure here does not prevent the loop.
    try:
        _run_gap_scan_once(prefix="startup scan")
    except Exception:
        logger.exception(
            "🔍 Hourly gap scan (startup scan) raised; "
            "continuing to interval loop"
        )

    while True:
        try:
            await wait_for_interval_hours(
                settings.HOURLY_GAP_SCAN_INTERVAL_HOURS,
                "hourly gap scan",
            )

            logger.info("🔍 Hourly gap scan scheduler woke up")

            try:
                _run_gap_scan_once(prefix="periodic scan")
            except Exception:
                # Keep the loop alive even if one scan fails.
                logger.exception(
                    "🔍 Hourly gap scan (periodic scan) raised; "
                    "will retry at next interval"
                )

        except asyncio.CancelledError:
            logger.info("Hourly gap scan scheduler cancelled")
            raise

        except Exception:
            logger.exception(
                "🔥 Hourly gap scan scheduler failed"
            )


# ============================================================
# REGIME BACKFILL SCHEDULER
# ============================================================


async def periodic_regime_backfill():
    """
    Backfill and maintain the macro_regimes historical table.

    The live path writes current_regime but never wrote
    macro_regimes, so the historical table is empty or stale.
    This task:

      1. On startup, if macro_regimes is empty, run a full
         backfill from DEFAULT_REGIME_BACKFILL_START (2017-08-17)
         to today.

      2. Then loop: run the backfill once per week, Sunday at
         03:00 UTC, to catch any gaps.

    The backfill itself is idempotent and guarded by an advisory
    lock (RegimeBackfillService), so overlapping with a CLI
    invocation is safe.

    Never raises out of the loop: any failure is logged and the
    task continues to the next scheduled run.
    """

    from app.services.regime_backfill_service import (
        DEFAULT_REGIME_BACKFILL_START,
        RegimeBackfillService,
    )

    logger.info("🗂️  Regime backfill scheduler started")

    # ========================================================
    # STARTUP RUN — only if macro_regimes is empty
    # ========================================================

    try:
        db = SessionLocal()
        try:
            from app.database.regime_repository import (
                RegimeRepository,
            )

            count = RegimeRepository(db).count_regimes()
        finally:
            db.close()

        if count == 0:
            logger.info(
                "🗂️  macro_regimes is empty; running initial "
                "backfill from %s",
                DEFAULT_REGIME_BACKFILL_START,
            )

            db = SessionLocal()
            try:
                service = RegimeBackfillService(db)
                result = await service.backfill_regimes(
                    start_date=DEFAULT_REGIME_BACKFILL_START,
                )
                logger.info(
                    "🗂️  Initial regime backfill result: %s",
                    result,
                )
            finally:
                db.close()
        else:
            logger.info(
                "🗂️  macro_regimes already populated (%d rows); "
                "skipping startup backfill",
                count,
            )

    except Exception:
        logger.exception(
            "🗂️  Initial regime backfill failed; "
            "will retry on the weekly schedule"
        )

    # ========================================================
    # WEEKLY LOOP — Sunday 03:00 UTC
    # ========================================================
    #
    # wait_until_next_run handles the daily rollover but not the
    # "which weekday" question, so we add a small check after
    # waking up: if today is not Sunday, sleep another day.

    while True:
        try:
            # Align to Sunday 03:00 UTC.
            while True:
                await wait_until_next_run(3, 0, "regime backfill")
                if datetime.now(timezone.utc).weekday() == 6:
                    # Monday=0 .. Sunday=6
                    break

            logger.info("🗂️  Regime backfill scheduler woke up")

            db = SessionLocal()
            try:
                service = RegimeBackfillService(db)
                result = await service.backfill_regimes(
                    start_date=DEFAULT_REGIME_BACKFILL_START,
                )
                logger.info(
                    "🗂️  Weekly regime backfill result: %s",
                    result,
                )
            finally:
                db.close()

            logger.info(
                "🗂️  Regime backfill scheduled job completed"
            )

        except asyncio.CancelledError:
            logger.info("Regime backfill scheduler cancelled")
            raise

        except Exception:
            logger.exception(
                "🔥 Regime backfill scheduler failed"
            )