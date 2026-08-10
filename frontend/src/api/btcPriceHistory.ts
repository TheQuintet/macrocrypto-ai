import type { ChartInterval } from '@/dashboard/chartInterval'
import {
  INTERVAL_DURATION_MS,
  MIN_LOOKBACK_MS_BY_INTERVAL,
} from '@/dashboard/chartInterval'
import type { TimeRange } from '@/stores/preferencesStore'

/**
 * Production-shaped history request.
 * Real gateway: GET /api/v1/btc/price/history?range=7d&interval=1h
 */
export type BtcPriceHistoryParams = {
  range: TimeRange
  interval: ChartInterval
}

/**
 * Production-shaped history candle/close point.
 * Expand with open/high/low later when OHLC charts land.
 */
export type BtcPriceHistoryPoint = {
  timestamp: string
  price: number
}

export type BtcPriceHistoryResponse = {
  range: TimeRange
  interval: ChartInterval
  points: BtcPriceHistoryPoint[]
}

export function btcPriceHistoryQueryKey(params: BtcPriceHistoryParams) {
  return ['btc-price-history', params.range, params.interval] as const
}

const MOCK_LATENCY_MS = 280
const MAX_POINTS = 500
const MINUTE_MS = 60_000

const RANGE_LOOKBACK_MS: Record<TimeRange, number> = {
  '24h': 24 * 60 * MINUTE_MS,
  '7d': 7 * 24 * 60 * MINUTE_MS,
  '30d': 30 * 24 * 60 * MINUTE_MS,
  '90d': 90 * 24 * 60 * MINUTE_MS,
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * Simulated history API: returns chart-ready points already bucketed
 * by `interval` for the requested `range` (server-side aggregation).
 */
export async function fetchBtcPriceHistory(
  params: BtcPriceHistoryParams,
  endMs = Date.now(),
): Promise<BtcPriceHistoryResponse> {
  await delay(MOCK_LATENCY_MS)

  const lookbackMs = Math.max(
    RANGE_LOOKBACK_MS[params.range],
    MIN_LOOKBACK_MS_BY_INTERVAL[params.interval],
  )
  const intervalMs = INTERVAL_DURATION_MS[params.interval]
  const startMs = endMs - lookbackMs

  const idealCount = Math.floor(lookbackMs / intervalMs) + 1
  const stepMs =
    idealCount <= MAX_POINTS
      ? intervalMs
      : Math.ceil(lookbackMs / (MAX_POINTS - 1) / intervalMs) * intervalMs

  const points: BtcPriceHistoryPoint[] = []
  let price = 64_000

  for (
    let timestampMs = startMs, index = 0;
    timestampMs <= endMs;
    timestampMs += stepMs, index += 1
  ) {
    price = nextDeterministicPrice(price, index)
    points.push({
      timestamp: new Date(timestampMs).toISOString(),
      price: Math.round(price * 100) / 100,
    })
  }

  return {
    range: params.range,
    interval: params.interval,
    points,
  }
}

function nextDeterministicPrice(previous: number, index: number) {
  const drift =
    Math.sin(index / 12) * 45 +
    Math.cos(index / 40) * 18 +
    ((index % 9) - 4) * 3
  return Math.max(1, previous + drift)
}
