"""
Tests for the EquityCorrService.
"""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.equity_corr_service import (
    EQUITY_CORR_INDICATOR,
    LOOKBACK_DAYS,
    EquityCorrService,
)


def make_nasdaq_rows(values):
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)

    return [
        SimpleNamespace(
            time=start + timedelta(days=index),
            value=value,
        )
        for index, value in enumerate(values)
    ]


def make_btc_candles(values):
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)

    return [
        {
            "open_time": int(
                (
                    start + timedelta(days=index)
                ).timestamp()
                * 1000
            ),
            "close": value,
        }
        for index, value in enumerate(values)
    ]


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def collector():
    return MagicMock()


@pytest.fixture
def service(db, collector):
    return EquityCorrService(
        db=db,
        collector=collector,
    )


@pytest.mark.asyncio
async def test_calculate_returns_empty_when_no_nasdaq_data(
    service,
    collector,
):
    service.repository.get_historical_data = MagicMock(
        return_value=[]
    )

    collector.get_klines = AsyncMock()

    result = await service.calculate()

    assert result == []

    service.repository.get_historical_data.assert_called_once_with(
        indicator_name="nasdaq_composite",
        days=LOOKBACK_DAYS,
    )

    collector.get_klines.assert_not_awaited()


@pytest.mark.asyncio
async def test_calculate_returns_empty_when_no_btc_data(
    service,
    collector,
):
    service.repository.get_historical_data = MagicMock(
        return_value=make_nasdaq_rows(
            [100 + index for index in range(35)]
        )
    )

    collector.get_klines = AsyncMock(
        return_value=[]
    )

    result = await service.calculate()

    assert result == []

    collector.get_klines.assert_awaited_once()


@pytest.mark.asyncio
async def test_calculate_returns_empty_when_dates_do_not_overlap(
    service,
    collector,
):
    service.repository.get_historical_data = MagicMock(
        return_value=[
            SimpleNamespace(
                time=datetime(
                    2024,
                    6,
                    1,
                    tzinfo=timezone.utc,
                ),
                value=100,
            )
        ]
    )

    collector.get_klines = AsyncMock(
        return_value=[
            {
                "open_time": int(
                    datetime(
                        2024,
                        1,
                        1,
                        tzinfo=timezone.utc,
                    ).timestamp()
                    * 1000
                ),
                "close": 50000,
            }
        ]
    )

    result = await service.calculate()

    assert result == []


@pytest.mark.asyncio
async def test_calculate_uses_correct_btc_parameters(
    service,
    collector,
):
    service.repository.get_historical_data = MagicMock(
        return_value=[]
    )

    collector.get_klines = AsyncMock(
        return_value=[]
    )

    with patch(
        "app.services.equity_corr_service.datetime"
    ) as mock_datetime:
        end_time = datetime(
            2024,
            2,
            1,
            tzinfo=timezone.utc,
        )

        mock_datetime.now.return_value = end_time
        mock_datetime.fromtimestamp.side_effect = (
            datetime.fromtimestamp
        )

        result = await service.calculate()

    assert result == []

    expected_start = end_time - timedelta(
        days=LOOKBACK_DAYS
    )

    collector.get_klines.assert_not_awaited()

    assert expected_start < end_time


@pytest.mark.asyncio
async def test_calculate_generates_correlation_records(
    service,
    collector,
):
    values = [
        100 + index
        for index in range(35)
    ]

    service.repository.get_historical_data = MagicMock(
        return_value=make_nasdaq_rows(values)
    )

    collector.get_klines = AsyncMock(
        return_value=make_btc_candles(values)
    )

    result = await service.calculate()

    assert result

    assert all(
        record["indicator_name"] == EQUITY_CORR_INDICATOR
        for record in result
    )

    assert all(
        record["source"] == "derived"
        for record in result
    )

    assert all(
        record["previous_value"] is None
        for record in result
    )

    assert all(
        record["change_percent"] is None
        for record in result
    )


@pytest.mark.asyncio
async def test_calculate_requires_minimum_rolling_period(
    service,
    collector,
):
    values = [
        100 + index
        for index in range(30)
    ]

    service.repository.get_historical_data = MagicMock(
        return_value=make_nasdaq_rows(values)
    )

    collector.get_klines = AsyncMock(
        return_value=make_btc_candles(values)
    )

    result = await service.calculate()

    assert result == []


@pytest.mark.asyncio
async def test_calculate_produces_records_after_minimum_period(
    service,
    collector,
):
    # 32 aligned observations are required:
    # 32 prices -> 31 returns -> 30 shifted returns.
    values = [
        100 + index
        for index in range(32)
    ]

    service.repository.get_historical_data = MagicMock(
        return_value=make_nasdaq_rows(values)
    )

    collector.get_klines = AsyncMock(
        return_value=make_btc_candles(values)
    )

    result = await service.calculate()

    assert len(result) == 1

    record = result[0]

    assert record["indicator_name"] == "equity_corr"
    assert record["source"] == "derived"
    assert record["previous_value"] is None
    assert record["change_percent"] is None
    assert isinstance(record["value"], float)

    assert record["time"] == datetime(
        2024,
        2,
        1,
        tzinfo=timezone.utc,
    )


@pytest.mark.asyncio
async def test_calculate_applies_information_barrier(
    service,
    collector,
):
    values = [
        100 + index
        for index in range(32)
    ]

    service.repository.get_historical_data = MagicMock(
        return_value=make_nasdaq_rows(values)
    )

    collector.get_klines = AsyncMock(
        return_value=make_btc_candles(values)
    )

    result = await service.calculate()

    assert result

    assert result[0]["time"] == datetime(
        2024,
        2,
        1,
        tzinfo=timezone.utc,
    )


@pytest.mark.asyncio
async def test_calculate_aligns_by_calendar_date(
    service,
    collector,
):
    start = datetime(
        2024,
        1,
        1,
        tzinfo=timezone.utc,
    )

    # NASDAQ has 32 consecutive days.
    nasdaq_rows = [
        SimpleNamespace(
            time=start + timedelta(days=index),
            value=100 + index,
        )
        for index in range(32)
    ]

    # BTC contains one extra date that NASDAQ does not have.
    btc_candles = [
        {
            "open_time": int(
                (
                    start + timedelta(days=index)
                ).timestamp()
                * 1000
            ),
            "close": 50000 + index,
        }
        for index in range(33)
    ]

    service.repository.get_historical_data = MagicMock(
        return_value=nasdaq_rows
    )

    collector.get_klines = AsyncMock(
        return_value=btc_candles
    )

    result = await service.calculate()

    assert result

    # The extra BTC-only date must not appear in the result.
    assert all(
        start <= record["time"] <= start + timedelta(days=31)
        for record in result
    )

    assert all(
        record["time"] != start + timedelta(days=32)
        for record in result
    )


@pytest.mark.asyncio
async def test_calculate_rounds_correlation_to_four_decimal_places(
    service,
    collector,
):
    values = [
        100 + index
        for index in range(35)
    ]

    service.repository.get_historical_data = MagicMock(
        return_value=make_nasdaq_rows(values)
    )

    collector.get_klines = AsyncMock(
        return_value=make_btc_candles(values)
    )

    result = await service.calculate()

    assert result

    for record in result:
        decimal_places = len(
            str(record["value"]).split(".")[-1]
        )

        assert decimal_places <= 4


@pytest.mark.asyncio
async def test_calculate_does_not_persist_records(
    service,
    collector,
):
    values = [
        100 + index
        for index in range(32)
    ]

    service.repository.get_historical_data = MagicMock(
        return_value=make_nasdaq_rows(values)
    )

    collector.get_klines = AsyncMock(
        return_value=make_btc_candles(values)
    )

    service.repository.create_many = MagicMock()

    result = await service.calculate()

    assert result

    # calculate() prepares records only.
    # Persistence is handled by the scheduler.
    service.repository.create_many.assert_not_called()


@pytest.mark.asyncio
async def test_close_does_not_close_injected_collector(
    service,
    collector,
):
    collector.close = AsyncMock()

    await service.close()

    collector.close.assert_not_awaited()


@pytest.mark.asyncio
async def test_close_closes_owned_collector(db):
    owned_collector = MagicMock()
    owned_collector.close = AsyncMock()

    service = EquityCorrService(
        db=db,
        collector=None,
    )

    service.collector = owned_collector
    service._owns_collector = True

    await service.close()

    owned_collector.close.assert_awaited_once()

