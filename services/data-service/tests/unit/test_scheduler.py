"""
Unit tests for app.services.scheduler.

Coverage:
- wait_until_next_run()
- periodic_macro_collection()
- periodic_regime_collection()
- QA interval mode
- production schedule mode
- current regime processing
- regime performance QA mode
- regime event QA mode
- similar historical period processing
- service/database cleanup
- cancellation handling
- error handling
"""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

import app.services.scheduler as scheduler


# ============================================================
# HELPERS
# ============================================================


def cancel_after_first_wait(monkeypatch):
    """
    Make the scheduler complete exactly one iteration and then
    cancel on the next wait.
    """
    calls = 0

    async def fake_wait(*args, **kwargs):
        nonlocal calls

        calls += 1

        if calls == 1:
            return

        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler,
        "wait_until_next_run",
        fake_wait,
    )

    return calls


def sleep_once_then_cancel(monkeypatch):
    """
    Make an interval-based scheduler complete exactly one
    iteration and then cancel on the next sleep.
    """
    calls = 0

    async def fake_sleep(*args, **kwargs):
        nonlocal calls

        calls += 1

        if calls == 1:
            return

        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    return calls


# ============================================================
# wait_until_next_run
# ============================================================


@pytest.mark.asyncio
async def test_wait_until_next_run_sleeps_until_future_time(
    monkeypatch,
):
    """
    The helper should calculate the next scheduled UTC time
    and pass a non-negative delay to asyncio.sleep().
    """

    sleep_mock = AsyncMock()

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        sleep_mock,
    )

    await scheduler.wait_until_next_run(
        hour=23,
        minute=59,
        job_name="test job",
    )

    sleep_mock.assert_awaited_once()

    wait_seconds = sleep_mock.await_args.args[0]

    assert wait_seconds >= 0


@pytest.mark.asyncio
async def test_wait_until_next_run_logs_job_name(
    monkeypatch,
    caplog,
):
    """
    The helper should log the scheduled job name.
    """

    sleep_mock = AsyncMock()

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        sleep_mock,
    )

    with caplog.at_level(
        "INFO",
        logger="app.services.scheduler",
    ):
        await scheduler.wait_until_next_run(
            hour=12,
            minute=30,
            job_name="test scheduler",
        )

    assert any(
        "test scheduler" in record.message
        for record in caplog.records
    )


# ============================================================
# MACRO/FRED SCHEDULER
# ============================================================


@pytest.mark.asyncio
async def test_periodic_macro_collection_interval_mode(
    monkeypatch,
):
    """
    MACRO_UPDATE_INTERVAL_MINUTES > 0 should use interval mode.
    """

    monkeypatch.setattr(
        scheduler.settings,
        "MACRO_UPDATE_INTERVAL_MINUTES",
        1,
    )

    sleep_calls = 0

    async def fake_sleep(seconds):
        nonlocal sleep_calls

        sleep_calls += 1

        if sleep_calls == 1:
            assert seconds == 60
            return

        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    with pytest.raises(asyncio.CancelledError):
        await scheduler.periodic_macro_collection()


@pytest.mark.asyncio
async def test_periodic_macro_collection_production_mode(
    monkeypatch,
):
    """
    MACRO_UPDATE_INTERVAL_MINUTES == 0 should use the configured
    daily UTC schedule.
    """

    monkeypatch.setattr(
        scheduler.settings,
        "MACRO_UPDATE_INTERVAL_MINUTES",
        0,
    )

    calls = 0

    async def fake_wait(hour, minute, job_name):
        nonlocal calls

        calls += 1

        assert hour == scheduler.settings.MACRO_UPDATE_HOUR_UTC
        assert minute == scheduler.settings.MACRO_UPDATE_MINUTE_UTC
        assert job_name == "macro/FRED update"

        if calls > 1:
            raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler,
        "wait_until_next_run",
        fake_wait,
    )

    with pytest.raises(asyncio.CancelledError):
        await scheduler.periodic_macro_collection()

    assert calls == 2


@pytest.mark.asyncio
async def test_periodic_macro_collection_logs_completion(
    monkeypatch,
    caplog,
):
    """
    A successful macro scheduler iteration should log completion.
    """

    monkeypatch.setattr(
        scheduler.settings,
        "MACRO_UPDATE_INTERVAL_MINUTES",
        1,
    )

    calls = 0

    async def fake_sleep(seconds):
        nonlocal calls

        calls += 1

        if calls == 1:
            return

        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    with caplog.at_level(
        "INFO",
        logger="app.services.scheduler",
    ):
        with pytest.raises(asyncio.CancelledError):
            await scheduler.periodic_macro_collection()

    assert any(
        "Macro/FRED scheduled job completed" in record.message
        for record in caplog.records
    )


@pytest.mark.asyncio
async def test_periodic_macro_collection_handles_cancellation(
    monkeypatch,
    caplog,
):
    """
    Cancellation should be logged and re-raised.
    """

    monkeypatch.setattr(
        scheduler.settings,
        "MACRO_UPDATE_INTERVAL_MINUTES",
        1,
    )

    async def fake_sleep(seconds):
        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    with caplog.at_level(
        "INFO",
        logger="app.services.scheduler",
    ):
        with pytest.raises(asyncio.CancelledError):
            await scheduler.periodic_macro_collection()

    assert any(
        "Macro/FRED scheduler cancelled" in record.message
        for record in caplog.records
    )


# ============================================================
# CURRENT REGIME SCHEDULER - BASIC FLOW
# ============================================================


@pytest.mark.asyncio
async def test_periodic_regime_collection_interval_mode(
    monkeypatch,
):
    """
    CURRENT_REGIME_UPDATE_INTERVAL_MINUTES > 0 should use
    interval mode.
    """

    monkeypatch.setattr(
        scheduler.settings,
        "CURRENT_REGIME_UPDATE_INTERVAL_MINUTES",
        1,
    )

    sleep_calls = 0

    async def fake_sleep(seconds):
        nonlocal sleep_calls

        sleep_calls += 1

        if sleep_calls == 1:
            assert seconds == 60
            return

        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    with pytest.raises(asyncio.CancelledError):
        await scheduler.periodic_regime_collection()


@pytest.mark.asyncio
async def test_periodic_regime_collection_production_mode(
    monkeypatch,
):
    """
    CURRENT_REGIME_UPDATE_INTERVAL_MINUTES == 0 should use
    wait_until_next_run().
    """

    monkeypatch.setattr(
        scheduler.settings,
        "CURRENT_REGIME_UPDATE_INTERVAL_MINUTES",
        0,
    )

    calls = 0

    async def fake_wait(hour, minute, job_name):
        nonlocal calls

        calls += 1

        assert (
            hour
            == scheduler.settings.CURRENT_REGIME_UPDATE_HOUR_UTC
        )

        assert (
            minute
            == scheduler.settings.CURRENT_REGIME_UPDATE_MINUTE_UTC
        )

        assert job_name == "current regime update"

        if calls > 1:
            raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler,
        "wait_until_next_run",
        fake_wait,
    )

    with pytest.raises(asyncio.CancelledError):
        await scheduler.periodic_regime_collection()

    assert calls == 2


# ============================================================
# CURRENT REGIME PROCESSING
# ============================================================


@pytest.mark.asyncio
async def test_periodic_regime_collection_processes_current_regime(
    monkeypatch,
):
    """
    The scheduler should create CurrentRegimeService and call
    process_current_regime().
    """

    monkeypatch.setattr(
        scheduler.settings,
        "CURRENT_REGIME_UPDATE_INTERVAL_MINUTES",
        1,
    )

    # Disable optional branches.
    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_PERFORMANCE_QA_MODE",
        False,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_EVENT_QA_MODE",
        False,
    )

    db = MagicMock()

    monkeypatch.setattr(
        "app.database.session.SessionLocal",
        lambda: db,
    )

    service = MagicMock()

    service.process_current_regime = AsyncMock(
        return_value="growth"
    )

    service.close = AsyncMock()

    monkeypatch.setattr(
        "app.services.current_regime_service.CurrentRegimeService",
        lambda database: service,
    )

    sleep_calls = 0

    async def fake_sleep(seconds):
        nonlocal sleep_calls

        sleep_calls += 1

        if sleep_calls == 1:
            return

        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    with pytest.raises(asyncio.CancelledError):
        await scheduler.periodic_regime_collection()

    service.process_current_regime.assert_awaited_once()
    service.close.assert_awaited_once()
    db.close.assert_called_once()


@pytest.mark.asyncio
async def test_periodic_regime_collection_handles_no_current_regime(
    monkeypatch,
):
    """
    If process_current_regime() returns None, optional downstream
    processing should be skipped.
    """

    monkeypatch.setattr(
        scheduler.settings,
        "CURRENT_REGIME_UPDATE_INTERVAL_MINUTES",
        1,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_PERFORMANCE_QA_MODE",
        True,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_EVENT_QA_MODE",
        True,
    )

    db = MagicMock()

    monkeypatch.setattr(
        "app.database.session.SessionLocal",
        lambda: db,
    )

    service = MagicMock()

    service.process_current_regime = AsyncMock(
        return_value=None
    )

    service.close = AsyncMock()

    monkeypatch.setattr(
        "app.services.current_regime_service.CurrentRegimeService",
        lambda database: service,
    )

    sleep_calls = 0

    async def fake_sleep(seconds):
        nonlocal sleep_calls

        sleep_calls += 1

        if sleep_calls == 1:
            return

        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    with pytest.raises(asyncio.CancelledError):
        await scheduler.periodic_regime_collection()

    service.process_current_regime.assert_awaited_once()
    service.close.assert_awaited_once()
    db.close.assert_called_once()


# ============================================================
# REGIME PERFORMANCE
# ============================================================


@pytest.mark.asyncio
async def test_periodic_regime_collection_performance_qa_mode(
    monkeypatch,
):
    """
    When REGIME_PERFORMANCE_QA_MODE is enabled and a current
    regime exists, regime performance should be calculated.
    """

    monkeypatch.setattr(
        scheduler.settings,
        "CURRENT_REGIME_UPDATE_INTERVAL_MINUTES",
        1,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_PERFORMANCE_QA_MODE",
        True,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_EVENT_QA_MODE",
        False,
    )

    db = MagicMock()

    monkeypatch.setattr(
        "app.database.session.SessionLocal",
        lambda: db,
    )

    service = MagicMock()

    current_regime = MagicMock()

    service.process_current_regime = AsyncMock(
        return_value=current_regime
    )

    service.close = AsyncMock()

    monkeypatch.setattr(
        "app.services.current_regime_service.CurrentRegimeService",
        lambda database: service,
    )

    macro_regime = MagicMock()

    repository = MagicMock()

    repository.get_current_regime.return_value = macro_regime

    monkeypatch.setattr(
        "app.database.regime_repository.RegimeRepository",
        lambda database: repository,
    )

    performance_service = MagicMock()

    performance_service.calculate_regime_performance.return_value = {
        "status": "success"
    }

    monkeypatch.setattr(
        "app.services.regime_performance_service.RegimePerformanceService",
        lambda database: performance_service,
    )

    sleep_calls = 0

    async def fake_sleep(seconds):
        nonlocal sleep_calls

        sleep_calls += 1

        if sleep_calls == 1:
            return

        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    with pytest.raises(asyncio.CancelledError):
        await scheduler.periodic_regime_collection()

    repository.get_current_regime.assert_called_once()

    performance_service.calculate_regime_performance.assert_called_once_with(
        macro_regime
    )


@pytest.mark.asyncio
async def test_periodic_regime_collection_skips_performance_when_disabled(
    monkeypatch,
):
    """
    REGIME_PERFORMANCE_QA_MODE=False should skip performance
    processing.
    """

    monkeypatch.setattr(
        scheduler.settings,
        "CURRENT_REGIME_UPDATE_INTERVAL_MINUTES",
        1,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_PERFORMANCE_QA_MODE",
        False,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_EVENT_QA_MODE",
        False,
    )

    db = MagicMock()

    monkeypatch.setattr(
        "app.database.session.SessionLocal",
        lambda: db,
    )

    service = MagicMock()

    service.process_current_regime = AsyncMock(
        return_value=MagicMock()
    )

    service.close = AsyncMock()

    monkeypatch.setattr(
        "app.services.current_regime_service.CurrentRegimeService",
        lambda database: service,
    )

    repository = MagicMock()

    monkeypatch.setattr(
        "app.database.regime_repository.RegimeRepository",
        lambda database: repository,
    )

    performance_service = MagicMock()

    monkeypatch.setattr(
        "app.services.regime_performance_service.RegimePerformanceService",
        lambda database: performance_service,
    )

    sleep_calls = 0

    async def fake_sleep(seconds):
        nonlocal sleep_calls

        sleep_calls += 1

        if sleep_calls == 1:
            return

        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    with pytest.raises(asyncio.CancelledError):
        await scheduler.periodic_regime_collection()

    repository.get_current_regime.assert_not_called()
    performance_service.calculate_regime_performance.assert_not_called()


# ============================================================
# REGIME EVENT ANALYSIS
# ============================================================


@pytest.mark.asyncio
async def test_periodic_regime_collection_event_analysis_enabled(
    monkeypatch,
):
    """
    REGIME_EVENT_QA_MODE=True should process the current regime
    event.
    """

    monkeypatch.setattr(
        scheduler.settings,
        "CURRENT_REGIME_UPDATE_INTERVAL_MINUTES",
        1,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_PERFORMANCE_QA_MODE",
        False,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_EVENT_QA_MODE",
        True,
    )

    db = MagicMock()

    monkeypatch.setattr(
        "app.database.session.SessionLocal",
        lambda: db,
    )

    service = MagicMock()

    current_regime = MagicMock()

    service.process_current_regime = AsyncMock(
        return_value=current_regime
    )

    service.close = AsyncMock()

    monkeypatch.setattr(
        "app.services.current_regime_service.CurrentRegimeService",
        lambda database: service,
    )

    event_service = MagicMock()

    event_service.process_current_regime_event.return_value = {
        "status": "success"
    }

    monkeypatch.setattr(
        "app.services.regime_event_service.RegimeEventService",
        lambda database: event_service,
    )

    sleep_calls = 0

    async def fake_sleep(seconds):
        nonlocal sleep_calls

        sleep_calls += 1

        if sleep_calls == 1:
            return

        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    with pytest.raises(asyncio.CancelledError):
        await scheduler.periodic_regime_collection()

    event_service.process_current_regime_event.assert_called_once_with(
        current_regime
    )


@pytest.mark.asyncio
async def test_periodic_regime_collection_skips_event_analysis_when_disabled(
    monkeypatch,
):
    """
    REGIME_EVENT_QA_MODE=False should skip event analysis.
    """

    monkeypatch.setattr(
        scheduler.settings,
        "CURRENT_REGIME_UPDATE_INTERVAL_MINUTES",
        1,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_PERFORMANCE_QA_MODE",
        False,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_EVENT_QA_MODE",
        False,
    )

    db = MagicMock()

    monkeypatch.setattr(
        "app.database.session.SessionLocal",
        lambda: db,
    )

    service = MagicMock()

    service.process_current_regime = AsyncMock(
        return_value=MagicMock()
    )

    service.close = AsyncMock()

    monkeypatch.setattr(
        "app.services.current_regime_service.CurrentRegimeService",
        lambda database: service,
    )

    event_service = MagicMock()

    monkeypatch.setattr(
        "app.services.regime_event_service.RegimeEventService",
        lambda database: event_service,
    )

    sleep_calls = 0

    async def fake_sleep(seconds):
        nonlocal sleep_calls

        sleep_calls += 1

        if sleep_calls == 1:
            return

        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    with pytest.raises(asyncio.CancelledError):
        await scheduler.periodic_regime_collection()

    event_service.process_current_regime_event.assert_not_called()


# ============================================================
# SIMILAR HISTORICAL PERIODS
# ============================================================


@pytest.mark.asyncio
async def test_periodic_regime_collection_updates_similar_periods(
    monkeypatch,
):
    """
    Similar historical period analysis should run when a current
    regime exists.
    """

    monkeypatch.setattr(
        scheduler.settings,
        "CURRENT_REGIME_UPDATE_INTERVAL_MINUTES",
        1,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_PERFORMANCE_QA_MODE",
        False,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_EVENT_QA_MODE",
        False,
    )

    db = MagicMock()

    monkeypatch.setattr(
        "app.database.session.SessionLocal",
        lambda: db,
    )

    service = MagicMock()

    service.process_current_regime = AsyncMock(
        return_value=MagicMock()
    )

    service.close = AsyncMock()

    monkeypatch.setattr(
        "app.services.current_regime_service.CurrentRegimeService",
        lambda database: service,
    )

    similar_service = MagicMock()

    similar_service.find_similar_periods.return_value = {
        "matches": 3
    }

    monkeypatch.setattr(
        "app.services.similar_period_service.SimilarPeriodService",
        lambda database: similar_service,
    )

    sleep_calls = 0

    async def fake_sleep(seconds):
        nonlocal sleep_calls

        sleep_calls += 1

        if sleep_calls == 1:
            return

        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    with pytest.raises(asyncio.CancelledError):
        await scheduler.periodic_regime_collection()

    similar_service.find_similar_periods.assert_called_once()


# ============================================================
# RESOURCE CLEANUP
# ============================================================


@pytest.mark.asyncio
async def test_periodic_regime_collection_closes_resources(
    monkeypatch,
):
    """
    Database session and CurrentRegimeService resources should
    be cleaned up after a scheduled run.
    """

    monkeypatch.setattr(
        scheduler.settings,
        "CURRENT_REGIME_UPDATE_INTERVAL_MINUTES",
        1,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_PERFORMANCE_QA_MODE",
        False,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_EVENT_QA_MODE",
        False,
    )

    db = MagicMock()

    monkeypatch.setattr(
        "app.database.session.SessionLocal",
        lambda: db,
    )

    service = MagicMock()

    service.process_current_regime = AsyncMock(
        return_value=None
    )

    service.close = AsyncMock()

    monkeypatch.setattr(
        "app.services.current_regime_service.CurrentRegimeService",
        lambda database: service,
    )

    sleep_calls = 0

    async def fake_sleep(seconds):
        nonlocal sleep_calls

        sleep_calls += 1

        if sleep_calls == 1:
            return

        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    with pytest.raises(asyncio.CancelledError):
        await scheduler.periodic_regime_collection()

    service.close.assert_awaited_once()
    db.close.assert_called_once()


# ============================================================
# ERROR HANDLING
# ============================================================


@pytest.mark.asyncio
async def test_periodic_regime_collection_handles_service_error(
    monkeypatch,
    caplog,
):
    """
    Unexpected errors in the scheduler should be logged rather
    than crashing the background loop.
    """

    monkeypatch.setattr(
        scheduler.settings,
        "CURRENT_REGIME_UPDATE_INTERVAL_MINUTES",
        1,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_PERFORMANCE_QA_MODE",
        False,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_EVENT_QA_MODE",
        False,
    )

    db = MagicMock()

    monkeypatch.setattr(
        "app.database.session.SessionLocal",
        lambda: db,
    )

    service = MagicMock()

    service.process_current_regime = AsyncMock(
        side_effect=RuntimeError("test service failure")
    )

    service.close = AsyncMock()

    monkeypatch.setattr(
        "app.services.current_regime_service.CurrentRegimeService",
        lambda database: service,
    )

    sleep_calls = 0

    async def fake_sleep(seconds):
        nonlocal sleep_calls

        sleep_calls += 1

        if sleep_calls == 1:
            return

        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    with caplog.at_level(
        "ERROR",
        logger="app.services.scheduler",
    ):
        with pytest.raises(asyncio.CancelledError):
            await scheduler.periodic_regime_collection()

    assert any(
        "Current regime scheduler failed" in record.message
        for record in caplog.records
    )


@pytest.mark.asyncio
async def test_periodic_regime_collection_handles_performance_error(
    monkeypatch,
    caplog,
):
    """
    A regime performance failure should be logged without
    terminating the scheduler.
    """

    monkeypatch.setattr(
        scheduler.settings,
        "CURRENT_REGIME_UPDATE_INTERVAL_MINUTES",
        1,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_PERFORMANCE_QA_MODE",
        True,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_EVENT_QA_MODE",
        False,
    )

    db = MagicMock()

    monkeypatch.setattr(
        "app.database.session.SessionLocal",
        lambda: db,
    )

    service = MagicMock()

    service.process_current_regime = AsyncMock(
        return_value=MagicMock()
    )

    service.close = AsyncMock()

    monkeypatch.setattr(
        "app.services.current_regime_service.CurrentRegimeService",
        lambda database: service,
    )

    repository = MagicMock()

    repository.get_current_regime.return_value = MagicMock()

    monkeypatch.setattr(
        "app.database.regime_repository.RegimeRepository",
        lambda database: repository,
    )

    performance_service = MagicMock()

    performance_service.calculate_regime_performance.side_effect = (
        RuntimeError("performance failure")
    )

    monkeypatch.setattr(
        "app.services.regime_performance_service.RegimePerformanceService",
        lambda database: performance_service,
    )

    sleep_calls = 0

    async def fake_sleep(seconds):
        nonlocal sleep_calls

        sleep_calls += 1

        if sleep_calls == 1:
            return

        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    with caplog.at_level(
        "ERROR",
        logger="app.services.scheduler",
    ):
        with pytest.raises(asyncio.CancelledError):
            await scheduler.periodic_regime_collection()

    assert any(
        "Regime performance calculation failed" in record.message
        for record in caplog.records
    )


@pytest.mark.asyncio
async def test_periodic_regime_collection_handles_event_error(
    monkeypatch,
    caplog,
):
    """
    A regime event analysis failure should be logged without
    terminating the scheduler.
    """

    monkeypatch.setattr(
        scheduler.settings,
        "CURRENT_REGIME_UPDATE_INTERVAL_MINUTES",
        1,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_PERFORMANCE_QA_MODE",
        False,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_EVENT_QA_MODE",
        True,
    )

    db = MagicMock()

    monkeypatch.setattr(
        "app.database.session.SessionLocal",
        lambda: db,
    )

    service = MagicMock()

    service.process_current_regime = AsyncMock(
        return_value=MagicMock()
    )

    service.close = AsyncMock()

    monkeypatch.setattr(
        "app.services.current_regime_service.CurrentRegimeService",
        lambda database: service,
    )

    event_service = MagicMock()

    event_service.process_current_regime_event.side_effect = (
        RuntimeError("event failure")
    )

    monkeypatch.setattr(
        "app.services.regime_event_service.RegimeEventService",
        lambda database: event_service,
    )

    sleep_calls = 0

    async def fake_sleep(seconds):
        nonlocal sleep_calls

        sleep_calls += 1

        if sleep_calls == 1:
            return

        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    with caplog.at_level(
        "ERROR",
        logger="app.services.scheduler",
    ):
        with pytest.raises(asyncio.CancelledError):
            await scheduler.periodic_regime_collection()

    assert any(
        "Regime event analysis failed" in record.message
        for record in caplog.records
    )


@pytest.mark.asyncio
async def test_periodic_regime_collection_handles_similar_period_error(
    monkeypatch,
    caplog,
):
    """
    A similar-period analysis failure should be logged without
    terminating the scheduler.
    """

    monkeypatch.setattr(
        scheduler.settings,
        "CURRENT_REGIME_UPDATE_INTERVAL_MINUTES",
        1,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_PERFORMANCE_QA_MODE",
        False,
    )

    monkeypatch.setattr(
        scheduler.settings,
        "REGIME_EVENT_QA_MODE",
        False,
    )

    db = MagicMock()

    monkeypatch.setattr(
        "app.database.session.SessionLocal",
        lambda: db,
    )

    service = MagicMock()

    service.process_current_regime = AsyncMock(
        return_value=MagicMock()
    )

    service.close = AsyncMock()

    monkeypatch.setattr(
        "app.services.current_regime_service.CurrentRegimeService",
        lambda database: service,
    )

    similar_service = MagicMock()

    similar_service.find_similar_periods.side_effect = (
        RuntimeError("similar-period failure")
    )

    monkeypatch.setattr(
        "app.services.similar_period_service.SimilarPeriodService",
        lambda database: similar_service,
    )

    sleep_calls = 0

    async def fake_sleep(seconds):
        nonlocal sleep_calls

        sleep_calls += 1

        if sleep_calls == 1:
            return

        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    with caplog.at_level(
        "ERROR",
        logger="app.services.scheduler",
    ):
        with pytest.raises(asyncio.CancelledError):
            await scheduler.periodic_regime_collection()

    assert any(
        "Similar historical periods update failed" in record.message
        for record in caplog.records
    )


# ============================================================
# CANCELLATION
# ============================================================


@pytest.mark.asyncio
async def test_periodic_regime_collection_handles_cancellation(
    monkeypatch,
    caplog,
):
    """
    Scheduler cancellation should be logged and propagated.
    """

    monkeypatch.setattr(
        scheduler.settings,
        "CURRENT_REGIME_UPDATE_INTERVAL_MINUTES",
        1,
    )

    async def fake_sleep(seconds):
        raise asyncio.CancelledError

    monkeypatch.setattr(
        scheduler.asyncio,
        "sleep",
        fake_sleep,
    )

    with caplog.at_level(
        "INFO",
        logger="app.services.scheduler",
    ):
        with pytest.raises(asyncio.CancelledError):
            await scheduler.periodic_regime_collection()

    assert any(
        "Current regime scheduler cancelled" in record.message
        for record in caplog.records
    )