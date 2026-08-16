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


# ============================================================
# MACRO / FRED SCHEDULER
# ============================================================


async def periodic_macro_collection():
    """
    Scheduled macro/FRED data collection.

    QA/development:
        MACRO_UPDATE_INTERVAL_MINUTES > 0
        runs every N minutes.

    Production:
        MACRO_UPDATE_INTERVAL_MINUTES = 0
        uses the configured daily UTC schedule.

    NOTE:
        Keep the existing macro/FRED collection logic inside
        this function. The interval configuration only controls
        when the existing workflow executes.
    """

    logger.info(
        "📊 Macro/FRED scheduler started"
    )

    if settings.MACRO_UPDATE_INTERVAL_MINUTES > 0:

        logger.info(
            "Macro QA interval mode enabled: "
            "running every %s minute(s)",
            settings.MACRO_UPDATE_INTERVAL_MINUTES,
        )

    else:

        logger.info(
            "Macro production schedule mode enabled"
        )

    while True:

        try:

            # ==================================================
            # WAIT FOR NEXT MACRO EXECUTION
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
                    "macro/FRED update",
                )

            logger.info(
                "📊 Macro/FRED scheduler woke up"
            )

            # --------------------------------------------------
            # KEEP YOUR EXISTING MACRO/FRED COLLECTION WORKFLOW
            # HERE.
            #
            # Example:
            #
            # await collect_macro_data()
            #
            # Do not duplicate or change the existing collector
            # implementation here.
            # --------------------------------------------------

            logger.info(
                "📊 Macro/FRED scheduled job completed"
            )

        except asyncio.CancelledError:

            logger.info(
                "Macro/FRED scheduler cancelled"
            )

            raise

        except Exception:

            logger.exception(
                "🔥 Macro/FRED scheduler failed"
            )


# ============================================================
# CURRENT REGIME SCHEDULER
# ============================================================


# async def periodic_regime_collection():
#     """
#     Scheduled current macroeconomic regime processing.

#     QA/development:
#         CURRENT_REGIME_UPDATE_INTERVAL_MINUTES > 0
#         runs every N minutes.

#     Production:
#         CURRENT_REGIME_UPDATE_INTERVAL_MINUTES = 0
#         uses the configured daily UTC schedule.

#     Workflow:

#     1. Wait for configured QA interval or production schedule.
#     2. Process current macroeconomic regime.
#     3. Calculate/update BTC regime performance when enabled.
#     4. Process macro event analysis when enabled.
#     5. Update similar historical periods.
#     6. Clean up database/service resources.
#     7. Continue until cancelled.
#     """

#     logger.info(
#         "🔥 Current regime scheduler started"
#     )

#     # ========================================================
#     # CONFIGURATION STATUS
#     # ========================================================

#     if settings.CURRENT_REGIME_UPDATE_INTERVAL_MINUTES > 0:

#         logger.info(
#             "Current regime QA interval mode enabled: "
#             "running every %s minute(s)",
#             settings.CURRENT_REGIME_UPDATE_INTERVAL_MINUTES,
#         )

#     else:

#         logger.info(
#             "Current regime production schedule enabled: "
#             "running at %02d:%02d UTC",
#             settings.CURRENT_REGIME_UPDATE_HOUR_UTC,
#             settings.CURRENT_REGIME_UPDATE_MINUTE_UTC,
#         )

#     logger.info(
#         "Regime performance QA mode: %s",
#         settings.REGIME_PERFORMANCE_QA_MODE,
#     )

#     logger.info(
#         "Regime event QA mode: %s",
#         settings.REGIME_EVENT_QA_MODE,
#     )

#     # ========================================================
#     # IMPORTS
#     # ========================================================

#     from app.database.session import SessionLocal

#     from app.services.current_regime_service import (
#         CurrentRegimeService,
#     )

#     from app.services.regime_performance_service import (
#         RegimePerformanceService,
#     )

#     from app.services.similar_period_service import (
#         SimilarPeriodService,
#     )

#     # ========================================================
#     # MAIN LOOP
#     # ========================================================

#     while True:

#         try:

#             # ==================================================
#             # WAIT FOR NEXT REGIME EXECUTION
#             # ==================================================

#             if (
#                 settings.CURRENT_REGIME_UPDATE_INTERVAL_MINUTES
#                 > 0
#             ):

#                 await asyncio.sleep(
#                     settings.CURRENT_REGIME_UPDATE_INTERVAL_MINUTES
#                     * 60
#                 )

#             else:

#                 await wait_until_next_run(
#                     settings.CURRENT_REGIME_UPDATE_HOUR_UTC,
#                     settings.CURRENT_REGIME_UPDATE_MINUTE_UTC,
#                     "current regime update",
#                 )

#             logger.info(
#                 "🔥 Current regime scheduler woke up"
#             )

#             db = SessionLocal()
#             service = None

#             try:

#                 # ==================================================
#                 # 1. CURRENT REGIME CLASSIFICATION
#                 # ==================================================

#                 service = CurrentRegimeService(db)

#                 current_regime = (
#                     await service.process_current_regime()
#                 )

#                 logger.info(
#                     "Current regime processing completed: %s",
#                     current_regime,
#                 )

#                 # ==================================================
#                 # 2. REGIME PERFORMANCE
#                 # ==================================================

#                 if current_regime is not None:

#                     if settings.REGIME_PERFORMANCE_QA_MODE:

#                         logger.info(
#                             "📈 Regime performance QA mode enabled"
#                         )

#                         performance_service = (
#                             RegimePerformanceService(db)
#                         )

#                         try:

#                             performance_result = (
#                                 performance_service
#                                 .calculate_regime_performance(
#                                     current_regime
#                                 )
#                             )

#                             logger.info(
#                                 "Regime performance calculation "
#                                 "completed: %s",
#                                 performance_result,
#                             )

#                         except Exception:

#                             logger.exception(
#                                 "❌ Regime performance calculation failed"
#                             )

#                     else:

#                         logger.info(
#                             "Regime performance QA mode disabled; "
#                             "skipping regime_performance"
#                         )

#                 else:

#                     logger.info(
#                         "No current regime identified; "
#                         "skipping regime_performance"
#                     )

#                 # ==================================================
#                 # 3. REGIME EVENT ANALYSIS
#                 # ==================================================

#                 if current_regime is not None:

#                     if settings.REGIME_EVENT_QA_MODE:

#                         logger.info(
#                             "🧪 Regime event QA mode enabled"
#                         )

#                         try:

#                             from app.services.regime_event_service import (
#                                 RegimeEventService,
#                             )

#                             event_service = (
#                                 RegimeEventService(db)
#                             )

#                             if hasattr(
#                                 event_service,
#                                 "process_current_regime_event",
#                             ):

#                                 event_result = (
#                                     event_service
#                                     .process_current_regime_event(
#                                         current_regime
#                                     )
#                                 )

#                                 logger.info(
#                                     "Regime event analysis completed: %s",
#                                     event_result,
#                                 )

#                             else:

#                                 logger.info(
#                                     "RegimeEventService does not "
#                                     "implement "
#                                     "process_current_regime_event(); "
#                                     "skipping event analysis"
#                                 )

#                         except Exception:

#                             logger.exception(
#                                 "❌ Regime event analysis failed"
#                             )

#                     else:

#                         logger.info(
#                             "Regime event QA mode disabled; "
#                             "skipping regime_event_analysis"
#                         )

#                 else:

#                     logger.info(
#                         "No current regime identified; "
#                         "skipping regime_event_analysis"
#                     )

#                 # ==================================================
#                 # 4. SIMILAR HISTORICAL PERIODS
#                 # ==================================================

#                 if current_regime is not None:

#                     similar_service = (
#                         SimilarPeriodService(db)
#                     )

#                     try:

#                         similar_result = (
#                             similar_service.find_similar_periods()
#                         )

#                         logger.info(
#                             "Similar historical periods update "
#                             "completed: %s",
#                             similar_result,
#                         )

#                     except Exception:

#                         logger.exception(
#                             "❌ Similar historical periods update failed"
#                         )

#                 else:

#                     logger.info(
#                         "No current regime identified; "
#                         "skipping similar historical periods"
#                     )

#                 # ==================================================
#                 # COMPLETE
#                 # ==================================================

#                 logger.info(
#                     "🔥 Current regime scheduled job "
#                     "completed successfully"
#                 )

#             finally:

#                 if service:

#                     await service.close()

#                 db.close()

#                 logger.info(
#                     "Current regime database session closed"
#                 )

#         # ========================================================
#         # CANCELLATION
#         # ========================================================

#         except asyncio.CancelledError:

#             logger.info(
#                 "Current regime scheduler cancelled"
#             )

#             raise

#         # ========================================================
#         # UNEXPECTED ERROR
#         # ========================================================

#         except Exception:

#             logger.exception(
#                 "🔥 Current regime scheduler failed"
#             )

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