"""
Scheduled background jobs.

Responsibilities:
- Trigger macro/FRED updates using MACRO_UPDATE_INTERVAL_MINUTES.
- Trigger current macroeconomic regime classification.
- Trigger BTC regime performance calculation.
- Trigger similar historical period analysis.
- Optionally trigger macro event analysis in QA mode.
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

REGIME_EVENT_QA_MODE
    Enables regime_event_analysis processing during QA.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.database.session import SessionLocal
from app.services.economic_calendar_service import EconomicCalendarService
from app.services.indicator_service import IndicatorService
from app.services.equity_corr_service import EquityCorrService
from app.services.active_addresses_service import ActiveAddressesService
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
                        "📈 Active addresses calculation completed: " \
                        "📈 Persisted %d active_addresses records",
                        len(active_addresses_records),
                    )

                else:
                    logger.warning(
                        "📈 Active addresses calculation produced no records"
                    )

                

            finally:
                if equity_corr_service:
                    await equity_corr_service.close()
                if active_addresses_service:
                    await active_addresses_service.close()

                db.close()

            logger.info("📊 Macro/FRED scheduled job completed")

        except asyncio.CancelledError:
            logger.info("Macro/FRED scheduler cancelled")
            raise

        except Exception:
            logger.exception("🔥 Macro/FRED scheduler failed")
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

    1. Wait for configured QA interval orperiodic_macro_collection production schedule.
    2. Process current macroeconomic regime.
    3. Calculate/update BTC regime performance when enabled.
    4. Process macro event analysis when enabled.
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

    logger.info(
        "Regime event QA mode: %s",
        settings.REGIME_EVENT_QA_MODE,
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

    from app.services.regime_event_service import (
        RegimeEventService,
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
                # 2. REGIME PERFORMANCE
                # ==================================================

                # if current_regime is not None:

                #     if settings.REGIME_PERFORMANCE_QA_MODE:

                #         logger.info(
                #             "📈 Regime performance QA mode enabled"
                #         )

                #         performance_service = (
                #             RegimePerformanceService(db)
                #         )

                #         try:

                #             performance_result = (
                #                 performance_service
                #                 .calculate_regime_performance(
                #                     current_regime
                #                 )
                #             )

                #             logger.info(
                #                 "Regime performance calculation "
                #                 "completed: %s",
                #                 performance_result,
                #             )

                #         except Exception:

                #             logger.exception(
                #                 "❌ Regime performance calculation failed"
                #             )

                #     else:

                #         logger.info(
                #             "Regime performance QA mode disabled; "
                #             "skipping regime_performance"
                #         )

                # else:

                #     logger.info(
                #         "No current regime identified; "
                #         "skipping regime_performance"
                #     )

# ==================================================
# 2. REGIME PERFORMANCE
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
                # 3. REGIME EVENT ANALYSIS
                # ==================================================

                if current_regime is not None:

                    if settings.REGIME_EVENT_QA_MODE:

                        logger.info(
                            "🧪 Regime event QA mode enabled"
                        )

                        event_service = (
                            RegimeEventService(db)
                        )

                        try:

                            event_result = (
                                event_service
                                .process_current_regime_event(
                                    current_regime
                                )
                            )

                            logger.info(
                                "Regime event analysis completed: %s",
                                event_result,
                            )

                        except Exception:

                            logger.exception(
                                "❌ Regime event analysis failed"
                            )

                    else:

                        logger.info(
                            "Regime event QA mode disabled; "
                            "skipping regime_event_analysis"
                        )

                else:

                    logger.info(
                        "No current regime identified; "
                        "skipping regime_event_analysis"
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