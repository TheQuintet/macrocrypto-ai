import type { CandleInterval } from '@/types/chart'
import type { TimeRange } from '@/types/preferences'

const MINUTE_MS = 60_000
const DAY_MS = 24 * 60 * MINUTE_MS

export const TIME_RANGE_LOOKBACK_MS: Record<TimeRange, number> = {
  '30d': 30 * DAY_MS,
  '90d': 90 * DAY_MS,
  '1y': 365 * DAY_MS,
  '5y': 5 * 365 * DAY_MS,
}

/**
 * Daily candles smear across a year or more. Those ranges use weekly
 * buckets so the plot stays a candlestick chart.
 */
export function candleIntervalForTimeRange(range: TimeRange): CandleInterval {
  return range === '1y' || range === '5y' ? '1w' : '1d'
}

export function isCandleIntervalAllowed(
  range: TimeRange,
  interval: CandleInterval,
): boolean {
  return interval !== '1d' || candleIntervalForTimeRange(range) === '1d'
}
