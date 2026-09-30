"""
Unit tests for BTC price history service.

Tests cover:
- range/interval validation
- lookback calculation
- Binance interval selection
- candle merging
- candle capping
- yearly aggregation
- timestamp/point conversion
- history retrieval
- empty Binance responses
- custom/default max_points
- collector lifecycle
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.price_history_service import (
    BINANCE_MAX_LIMIT,
    DAY_MS,
    HOUR_MS,
    MIN_LOOKBACK_MS,
    MINUTE_MS,
    PriceHistoryService,
    PriceHistoryValidationError,
)
from app.config import settings


# ==========================================================
# HELPERS
# ==========================================================


def make_candle(
    open_time,
    open_price,
    high,
    low,
    close,
    close_time=None,
):
    """Create a lightweight Binance kline dictionary."""

    return {
        "open_time": open_time,
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "close_time": (
            close_time
            if close_time is not None
            else open_time + MINUTE_MS - 1
        ),
    }


@pytest.fixture
def collector():
    """Create a mocked Binance collector."""

    mock = MagicMock()
    mock.get_klines = AsyncMock()
    mock.close = AsyncMock()

    return mock


@pytest.fixture
def service(collector):
    """Create the service with an injected mock collector."""

    return PriceHistoryService(collector)


# ==========================================================
# LOOKBACK
# ==========================================================


def test_lookback_uses_range_when_range_is_larger(service):
    result = service.lookback_ms("24h", "1m")

    assert result == 45 * DAY_MS


def test_lookback_uses_interval_minimum_when_interval_requires_longer_window(
    service,
):
    result = service.lookback_ms("24h", "1h")

    assert result == MIN_LOOKBACK_MS["1h"]


def test_lookback_uses_larger_of_range_and_interval_floor(service):
    result = service.lookback_ms("30d", "1h")

    assert result == 30 * DAY_MS


@pytest.mark.parametrize(
    ("range_value", "interval", "expected"),
    [
        ("24h", "1m", 45 * DAY_MS),
        ("24h", "5m", 45 * DAY_MS),
        ("24h", "1h", 7 * DAY_MS),
        ("7d", "1d", 90 * DAY_MS),
        ("30d", "1d", 90 * DAY_MS),
        ("90d", "1w", 26 * 7 * DAY_MS),
        ("90d", "1y", 6 * 365 * DAY_MS),
    ],
)
def test_lookback_applies_interval_floor(
    service,
    range_value,
    interval,
    expected,
):
    assert service.lookback_ms(
        range_value,
        interval,
    ) == expected


# ==========================================================
# BINANCE INTERVAL SELECTION
# ==========================================================


@pytest.mark.parametrize(
    "interval",
    [
        "1m",
        "5m",
        "1h",
        "1d",
        "1w",
    ],
)
def test_choose_binance_interval_preserves_requested_interval(
    service,
    interval,
):
    assert (
        service.choose_binance_interval(
            interval,
            90 * DAY_MS,
        )
        == interval
    )


def test_choose_binance_interval_uses_monthly_for_one_year(
    service,
):
    assert (
        service.choose_binance_interval(
            "1y",
            6 * 365 * DAY_MS,
        )
        == "1M"
    )


# ==========================================================
# RANGE / INTERVAL VALIDATION
# ==========================================================


@pytest.mark.parametrize(
    "value",
    [
        "24h",
        "7d",
        "30d",
        "90d",
    ],
)
def test_parse_range_accepts_valid_ranges(service, value):
    assert service._parse_range(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "1d",
        "365d",
        "24H",
        "invalid",
        None,
    ],
)
def test_parse_range_rejects_invalid_ranges(service, value):
    with pytest.raises(PriceHistoryValidationError):
        service._parse_range(value)


def test_parse_range_error_contains_allowed_values(service):
    with pytest.raises(
        PriceHistoryValidationError,
        match="24h, 7d, 30d, 90d",
    ):
        service._parse_range("invalid")


@pytest.mark.parametrize(
    "value",
    [
        "1m",
        "5m",
        "1h",
        "1d",
        "1w",
        "1y",
    ],
)
def test_parse_interval_accepts_valid_intervals(service, value):
    assert service._parse_interval(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "2m",
        "10m",
        "1M",
        "1d ",
        "invalid",
        None,
    ],
)
def test_parse_interval_rejects_invalid_intervals(
    service,
    value,
):
    with pytest.raises(PriceHistoryValidationError):
        service._parse_interval(value)


def test_parse_interval_error_contains_allowed_values(service):
    with pytest.raises(
        PriceHistoryValidationError,
        match="1m, 5m, 1h, 1d, 1w, 1y",
    ):
        service._parse_interval("invalid")


# ==========================================================
# CANDLE MERGING
# ==========================================================


def test_merge_candles_uses_first_open_and_last_close(service):
    candles = [
        make_candle(1_000, 100, 110, 95, 105),
        make_candle(2_000, 105, 120, 100, 115),
        make_candle(3_000, 115, 125, 90, 120),
    ]

    result = service._merge_candles(candles)

    assert result["open_time"] == 1_000
    assert result["open"] == 100
    assert result["high"] == 125
    assert result["low"] == 90
    assert result["close"] == 120
    assert result["close_time"] == candles[-1]["close_time"]


def test_merge_candles_uses_last_open_time_when_close_time_missing(
    service,
):
    candles = [
        {
            "open_time": 1_000,
            "open": 100,
            "high": 110,
            "low": 95,
            "close": 105,
        },
        {
            "open_time": 2_000,
            "open": 105,
            "high": 120,
            "low": 100,
            "close": 115,
        },
    ]

    result = service._merge_candles(candles)

    assert result["close_time"] == 2_000


def test_merge_candles_with_single_candle(service):
    candle = make_candle(
        1_000,
        100,
        110,
        95,
        105,
    )

    result = service._merge_candles([candle])

    assert result["open_time"] == 1_000
    assert result["open"] == 100
    assert result["high"] == 110
    assert result["low"] == 95
    assert result["close"] == 105


# ==========================================================
# CANDLE CAPPING
# ==========================================================


def test_cap_candles_returns_same_list_when_under_limit(
    service,
):
    candles = [
        make_candle(1_000, 100, 110, 95, 105),
        make_candle(2_000, 105, 115, 100, 110),
    ]

    result = service.cap_candles(candles, 5)

    assert result == candles


def test_cap_candles_returns_empty_for_zero_limit(service):
    candles = [
        make_candle(1_000, 100, 110, 95, 105),
    ]

    assert service.cap_candles(candles, 0) == []


def test_cap_candles_returns_empty_for_negative_limit(service):
    candles = [
        make_candle(1_000, 100, 110, 95, 105),
    ]

    assert service.cap_candles(candles, -1) == []


def test_cap_candles_merges_candles_when_over_limit(
    service,
):
    candles = [
        make_candle(1_000, 100, 110, 95, 105),
        make_candle(2_000, 105, 120, 100, 115),
        make_candle(3_000, 115, 125, 90, 120),
        make_candle(4_000, 120, 130, 110, 125),
    ]

    result = service.cap_candles(candles, 2)

    assert len(result) == 2

    assert result[0]["open"] == 100
    assert result[0]["high"] == 120
    assert result[0]["low"] == 95
    assert result[0]["close"] == 115

    assert result[1]["open"] == 115
    assert result[1]["high"] == 130
    assert result[1]["low"] == 90
    assert result[1]["close"] == 125


def test_cap_candles_does_not_exceed_requested_max_points(
    service,
):
    candles = [
        make_candle(
            index * 1_000,
            100 + index,
            110 + index,
            90 + index,
            105 + index,
        )
        for index in range(11)
    ]

    result = service.cap_candles(candles, 3)

    assert len(result) <= 3


# ==========================================================
# YEARLY AGGREGATION
# ==========================================================


def test_aggregate_yearly_groups_candles_by_calendar_year(
    service,
):
    jan_2025 = int(
        datetime(
            2025,
            1,
            1,
            tzinfo=timezone.utc,
        ).timestamp()
        * 1000
    )

    jun_2025 = int(
        datetime(
            2025,
            6,
            1,
            tzinfo=timezone.utc,
        ).timestamp()
        * 1000
    )

    jan_2026 = int(
        datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ).timestamp()
        * 1000
    )

    candles = [
        make_candle(
            jan_2025,
            100,
            120,
            90,
            110,
        ),
        make_candle(
            jun_2025,
            110,
            130,
            100,
            125,
        ),
        make_candle(
            jan_2026,
            125,
            140,
            115,
            135,
        ),
    ]

    result = service.aggregate_yearly(candles)

    assert len(result) == 2

    assert result[0]["open_time"] == jan_2025
    assert result[0]["open"] == 100
    assert result[0]["high"] == 130
    assert result[0]["low"] == 90
    assert result[0]["close"] == 125

    assert result[1]["open_time"] == jan_2026
    assert result[1]["open"] == 125
    assert result[1]["high"] == 140
    assert result[1]["low"] == 115
    assert result[1]["close"] == 135


def test_aggregate_yearly_returns_empty_for_empty_input(
    service,
):
    assert service.aggregate_yearly([]) == []


# ==========================================================
# POINT CONVERSION
# ==========================================================


def test_timestamp_iso_returns_utc_iso_timestamp(service):
    timestamp = int(
        datetime(
            2026,
            1,
            1,
            12,
            30,
            tzinfo=timezone.utc,
        ).timestamp()
        * 1000
    )

    result = service._timestamp_iso(timestamp)

    assert result == "2026-01-01T12:30:00Z"


def test_to_points_converts_candles_to_response_points(
    service,
):
    timestamp = int(
        datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ).timestamp()
        * 1000
    )

    candles = [
        make_candle(
            timestamp,
            "100.5",
            "110.25",
            "95.75",
            "105.10",
        )
    ]

    result = service.to_points(candles)

    assert len(result) == 1

    point = result[0]

    assert point.timestamp == "2026-01-01T00:00:00Z"
    assert point.open == 100.5
    assert point.high == 110.25
    assert point.low == 95.75
    assert point.close == 105.10


def test_to_points_returns_empty_for_empty_candles(service):
    assert service.to_points([]) == []


# ==========================================================
# GET HISTORY
# ==========================================================


@pytest.mark.asyncio
async def test_get_history_fetches_expected_binance_parameters(
    service,
    collector,
):
    end_ms = 1_800_000_000_000

    candles = [
        make_candle(
            end_ms - 60_000,
            100,
            110,
            95,
            105,
        )
    ]

    collector.get_klines.return_value = candles

    result = await service.get_history(
        range_value="24h",
        interval="1h",
        end_ms=end_ms,
        max_points=100,
    )

    expected_window = service.lookback_ms(
        "24h",
        "1h",
    )

    collector.get_klines.assert_awaited_once_with(
        symbol=settings.BINANCE_DEFAULT_SYMBOL,
        interval="1h",
        limit=BINANCE_MAX_LIMIT,
        start_time=end_ms - expected_window,
        end_time=end_ms,
    )

    assert result.range == "24h"
    assert result.interval == "1h"
    assert len(result.points) == 1


@pytest.mark.asyncio
async def test_get_history_returns_empty_response_when_binance_returns_no_candles(
    service,
    collector,
):
    collector.get_klines.return_value = []

    result = await service.get_history(
        range_value="24h",
        interval="1h",
        end_ms=1_800_000_000_000,
        max_points=100,
    )

    assert result.range == "24h"
    assert result.interval == "1h"
    assert result.points == []


@pytest.mark.asyncio
async def test_get_history_uses_default_max_points(
    service,
    collector,
):
    candles = [
        make_candle(
            index * MINUTE_MS,
            100,
            110,
            90,
            105,
        )
        for index in range(5)
    ]

    collector.get_klines.return_value = candles

    result = await service.get_history(
        range_value="24h",
        interval="1m",
        end_ms=1_800_000_000_000,
    )

    assert result.points


@pytest.mark.asyncio
async def test_get_history_respects_custom_max_points(
    service,
    collector,
):
    candles = [
        make_candle(
            index * MINUTE_MS,
            100 + index,
            110 + index,
            90 + index,
            105 + index,
        )
        for index in range(20)
    ]

    collector.get_klines.return_value = candles

    result = await service.get_history(
        range_value="24h",
        interval="1m",
        end_ms=1_800_000_000_000,
        max_points=5,
    )

    assert len(result.points) <= 5


@pytest.mark.asyncio
async def test_get_history_zero_max_points_does_not_cap_candles(
    service,
    collector,
):
    candles = [
        make_candle(
            index * MINUTE_MS,
            100 + index,
            110 + index,
            90 + index,
            105 + index,
        )
        for index in range(10)
    ]

    collector.get_klines.return_value = candles

    result = await service.get_history(
        range_value="24h",
        interval="1m",
        end_ms=1_800_000_000_000,
        max_points=0,
    )

    assert len(result.points) == len(candles)


@pytest.mark.asyncio
async def test_get_history_uses_monthly_binance_interval_for_one_year(
    service,
    collector,
):
    end_ms = 1_800_000_000_000

    collector.get_klines.return_value = []

    result = await service.get_history(
        range_value="90d",
        interval="1y",
        end_ms=end_ms,
        max_points=100,
    )

    assert result.range == "90d"
    assert result.interval == "1y"

    collector.get_klines.assert_awaited_once()

    call_kwargs = collector.get_klines.call_args.kwargs

    assert call_kwargs["interval"] == "1M"


@pytest.mark.asyncio
async def test_get_history_aggregates_yearly_data_for_one_year_interval(
    service,
    collector,
):
    jan_2025 = int(
        datetime(
            2025,
            1,
            1,
            tzinfo=timezone.utc,
        ).timestamp()
        * 1000
    )

    jun_2025 = int(
        datetime(
            2025,
            6,
            1,
            tzinfo=timezone.utc,
        ).timestamp()
        * 1000
    )

    jan_2026 = int(
        datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ).timestamp()
        * 1000
    )

    collector.get_klines.return_value = [
        make_candle(
            jan_2025,
            100,
            120,
            90,
            110,
        ),
        make_candle(
            jun_2025,
            110,
            130,
            100,
            125,
        ),
        make_candle(
            jan_2026,
            125,
            140,
            115,
            135,
        ),
    ]

    result = await service.get_history(
        range_value="90d",
        interval="1y",
        end_ms=1_800_000_000_000,
        max_points=100,
    )

    assert len(result.points) == 2

    assert result.points[0].open == 100.0
    assert result.points[0].high == 130.0
    assert result.points[0].low == 90.0
    assert result.points[0].close == 125.0

    assert result.points[1].open == 125.0
    assert result.points[1].high == 140.0
    assert result.points[1].low == 115.0
    assert result.points[1].close == 135.0


@pytest.mark.asyncio
async def test_get_history_rejects_invalid_range(
    service,
    collector,
):
    with pytest.raises(PriceHistoryValidationError):
        await service.get_history(
            range_value="invalid",
            interval="1h",
        )

    collector.get_klines.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_history_rejects_invalid_interval(
    service,
    collector,
):
    with pytest.raises(PriceHistoryValidationError):
        await service.get_history(
            range_value="24h",
            interval="invalid",
        )

    collector.get_klines.assert_not_awaited()


# ==========================================================
# COLLECTOR LIFECYCLE
# ==========================================================


@pytest.mark.asyncio
async def test_close_closes_internally_owned_collector():
    collector = MagicMock()
    collector.close = AsyncMock()

    with patch(
        "app.services.price_history_service.BinanceCollector",
        return_value=collector,
    ):
        service = PriceHistoryService()

    await service.close()

    collector.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_does_not_close_injected_collector(
    collector,
):
    service = PriceHistoryService(collector)

    assert service._owns_collector is False

    await service.close()

    collector.close.assert_not_awaited()

