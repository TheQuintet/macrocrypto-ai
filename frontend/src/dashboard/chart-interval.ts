/** Candle / bucket size — independent from the time-range lookback window. */
export type ChartInterval = '1m' | '5m' | '1h' | '1d' | '1w' | '1y'

export const DEFAULT_CHART_INTERVAL: ChartInterval = '1h'

export const CHART_INTERVAL_OPTIONS: {
  value: ChartInterval
  label: string
}[] = [
  { value: '1m', label: '1m' },
  { value: '5m', label: '5m' },
  { value: '1h', label: '1h' },
  { value: '1d', label: '1d' },
  { value: '1w', label: '1w' },
  { value: '1y', label: '1y' },
]

const MINUTE_MS = 60_000
const HOUR_MS = 60 * MINUTE_MS
const DAY_MS = 24 * HOUR_MS

/** Minimum history so each interval can render multiple buckets. */
export const MIN_LOOKBACK_MS_BY_INTERVAL: Record<ChartInterval, number> = {
  '1m': 45 * DAY_MS,
  '5m': 45 * DAY_MS,
  '1h': 7 * DAY_MS,
  '1d': 90 * DAY_MS,
  '1w': 26 * 7 * DAY_MS,
  '1y': 6 * 365 * DAY_MS,
}

export const INTERVAL_DURATION_MS: Record<ChartInterval, number> = {
  '1m': MINUTE_MS,
  '5m': 5 * MINUTE_MS,
  '1h': HOUR_MS,
  '1d': DAY_MS,
  '1w': 7 * DAY_MS,
  '1y': 365 * DAY_MS,
}
