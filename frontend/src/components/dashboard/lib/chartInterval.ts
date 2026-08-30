import type { CandleInterval, ChartInterval } from '@/types/chart'

const MINUTE_MS = 60_000
const HOUR_MS = 60 * MINUTE_MS
const DAY_MS = 24 * HOUR_MS

export const INTERVAL_DURATION_MS: Record<ChartInterval, number> = {
  '1m': MINUTE_MS,
  '5m': 5 * MINUTE_MS,
  '1h': HOUR_MS,
  '1d': DAY_MS,
  '1w': 7 * DAY_MS,
  '1mo': 30 * DAY_MS,
  '1y': 365 * DAY_MS,
}

export const CANDLE_INTERVAL_LABELS: Record<ChartInterval, string> = {
  '1m': '1m',
  '5m': '5m',
  '1h': 'hourly',
  '1d': 'daily',
  '1w': 'weekly',
  '1mo': 'monthly',
  '1y': 'yearly',
}

export const CANDLE_INTERVAL_OPTIONS: {
  value: CandleInterval
  label: string
}[] = [
  { value: '1d', label: 'Daily' },
  { value: '1w', label: 'Weekly' },
]
