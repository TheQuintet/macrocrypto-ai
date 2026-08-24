"""
BTC OHLC history for the price chart.

Builds candles from Binance klines. Interval bucketing and the
point cap happen here so the frontend does not aggregate.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any

from app.api.schemas.price_response import (
    BtcPriceHistoryPoint,
    BtcPriceHistoryResponse,
    ChartInterval,
    TimeRange,
)
from app.collectors.binance import BinanceCollector
from app.config import settings

logger = logging.getLogger(__name__)

VALID_RANGES: tuple[TimeRange, ...] = ("24h", "7d", "30d", "90d")
VALID_INTERVALS: tuple[ChartInterval, ...] = (
    "1m",
    "5m",
    "1h",
    "1d",
    "1w",
    "1y",
)

MINUTE_MS = 60_000
HOUR_MS = 60 * MINUTE_MS
DAY_MS = 24 * HOUR_MS
WEEK_MS = 7 * DAY_MS
MONTH_MS = 30 * DAY_MS
YEAR_MS = 365 * DAY_MS

RANGE_LOOKBACK_MS: dict[TimeRange, int] = {
    "24h": 24 * HOUR_MS,
    "7d": 7 * DAY_MS,
    "30d": 30 * DAY_MS,
    "90d": 90 * DAY_MS,
}

INTERVAL_MS: dict[ChartInterval, int] = {
    "1m": MINUTE_MS,
    "5m": 5 * MINUTE_MS,
    "1h": HOUR_MS,
    "1d": DAY_MS,
    "1w": WEEK_MS,
    "1y": YEAR_MS,
}

# Same floors as frontend `MIN_LOOKBACK_MS_BY_INTERVAL` so a short
# range still yields more than one coarse bucket.
MIN_LOOKBACK_MS: dict[ChartInterval, int] = {
    "1m": 45 * DAY_MS,
    "5m": 45 * DAY_MS,
    "1h": 7 * DAY_MS,
    "1d": 90 * DAY_MS,
    "1w": 26 * WEEK_MS,
    "1y": 6 * YEAR_MS,
}

# Finest → coarsest Binance intervals we may fetch.
BINANCE_INTERVALS: tuple[tuple[str, int], ...] = (
    ("1m", MINUTE_MS),
    ("3m", 3 * MINUTE_MS),
    ("5m", 5 * MINUTE_MS),
    ("15m", 15 * MINUTE_MS),
    ("30m", 30 * MINUTE_MS),
    ("1h", HOUR_MS),
    ("2h", 2 * HOUR_MS),
    ("4h", 4 * HOUR_MS),
    ("6h", 6 * HOUR_MS),
    ("8h", 8 * HOUR_MS),
    ("12h", 12 * HOUR_MS),
    ("1d", DAY_MS),
    ("3d", 3 * DAY_MS),
    ("1w", WEEK_MS),
    ("1M", MONTH_MS),
)

BINANCE_MAX_LIMIT = 1000


class PriceHistoryValidationError(ValueError):
    """Invalid range or interval query."""


class PriceHistoryService:
    """Fetch, bucket, and cap OHLC candles for the chart API."""

    def __init__(self, collector: BinanceCollector | None = None):
        self.collector = collector or BinanceCollector()
        self._owns_collector = collector is None

    async def close(self) -> None:
        if self._owns_collector:
            await self.collector.close()

    def lookback_ms(self, range_value: TimeRange, interval: ChartInterval) -> int:
        return max(
            RANGE_LOOKBACK_MS[range_value],
            MIN_LOOKBACK_MS[interval],
        )

    def choose_binance_interval(
        self,
        interval: ChartInterval,
        lookback_ms: int,
    ) -> str:
        """
        Pick a Binance kline interval.

        Never finer than the requested chart interval. Coarsen when the
        window would exceed Binance's 1000-candle page size.
        """

        if interval == "1y":
            requested_ms = YEAR_MS
            native = "1M"
        else:
            requested_ms = INTERVAL_MS[interval]
            native = interval

        estimated = lookback_ms / requested_ms + 1

        if estimated <= BINANCE_MAX_LIMIT and interval != "1y":
            return native

        min_step_ms = max(
            requested_ms,
            lookback_ms / BINANCE_MAX_LIMIT,
        )

        for name, step_ms in BINANCE_INTERVALS:
            if step_ms >= min_step_ms:
                return name

        return "1M"

    def cap_candles(
        self,
        candles: list[dict[str, Any]],
        max_points: int,
    ) -> list[dict[str, Any]]:
        """Merge consecutive candles so the series stays within max_points."""

        if max_points < 1:
            return []

        if len(candles) <= max_points:
            return candles

        bucket_size = math.ceil(len(candles) / max_points)
        capped: list[dict[str, Any]] = []

        for start in range(0, len(candles), bucket_size):
            group = candles[start:start + bucket_size]
            capped.append(self._merge_candles(group))

        return capped[:max_points]

    def aggregate_yearly(
        self,
        candles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Collapse monthly (or finer) candles into calendar-year OHLC."""

        by_year: dict[int, list[dict[str, Any]]] = {}

        for candle in candles:
            year = datetime.fromtimestamp(
                candle["open_time"] / 1000,
                tz=timezone.utc,
            ).year
            by_year.setdefault(year, []).append(candle)

        return [
            self._merge_candles(by_year[year])
            for year in sorted(by_year)
        ]

    def to_points(
        self,
        candles: list[dict[str, Any]],
    ) -> list[BtcPriceHistoryPoint]:
        return [
            BtcPriceHistoryPoint(
                timestamp=self._timestamp_iso(candle["open_time"]),
                open=float(candle["open"]),
                high=float(candle["high"]),
                low=float(candle["low"]),
                close=float(candle["close"]),
            )
            for candle in candles
        ]

    async def get_history(
        self,
        range_value: str,
        interval: str,
        end_ms: int | None = None,
    ) -> BtcPriceHistoryResponse:
        chart_range = self._parse_range(range_value)
        chart_interval = self._parse_interval(interval)

        end_ms = end_ms or int(
            datetime.now(timezone.utc).timestamp() * 1000
        )
        window_ms = self.lookback_ms(chart_range, chart_interval)
        start_ms = end_ms - window_ms

        fetch_interval = self.choose_binance_interval(
            chart_interval,
            window_ms,
        )

        logger.info(
            "Fetching BTC history range=%s interval=%s "
            "binance_interval=%s",
            chart_range,
            chart_interval,
            fetch_interval,
        )

        candles = await self.collector.get_klines(
            symbol=settings.BINANCE_DEFAULT_SYMBOL,
            interval=fetch_interval,
            limit=BINANCE_MAX_LIMIT,
            start_time=start_ms,
            end_time=end_ms,
        )

        if not candles:
            logger.warning(
                "No BTC klines for range=%s interval=%s",
                chart_range,
                chart_interval,
            )
            return BtcPriceHistoryResponse(
                range=chart_range,
                interval=chart_interval,
                points=[],
            )

        if chart_interval == "1y":
            candles = self.aggregate_yearly(candles)

        candles = self.cap_candles(
            candles,
            settings.PRICE_HISTORY_MAX_POINTS,
        )

        return BtcPriceHistoryResponse(
            range=chart_range,
            interval=chart_interval,
            points=self.to_points(candles),
        )

    @staticmethod
    def _parse_range(value: str) -> TimeRange:
        if value not in VALID_RANGES:
            raise PriceHistoryValidationError(
                f"range must be one of {', '.join(VALID_RANGES)}"
            )
        return value  # type: ignore[return-value]

    @staticmethod
    def _parse_interval(value: str) -> ChartInterval:
        if value not in VALID_INTERVALS:
            raise PriceHistoryValidationError(
                f"interval must be one of {', '.join(VALID_INTERVALS)}"
            )
        return value  # type: ignore[return-value]

    @staticmethod
    def _timestamp_iso(open_time_ms: int) -> str:
        return (
            datetime.fromtimestamp(
                open_time_ms / 1000,
                tz=timezone.utc,
            )
            .isoformat()
            .replace("+00:00", "Z")
        )

    @staticmethod
    def _merge_candles(group: list[dict[str, Any]]) -> dict[str, Any]:
        first = group[0]
        last = group[-1]

        return {
            "open_time": first["open_time"],
            "open": first["open"],
            "high": max(candle["high"] for candle in group),
            "low": min(candle["low"] for candle in group),
            "close": last["close"],
            "close_time": last.get("close_time", last["open_time"]),
        }
