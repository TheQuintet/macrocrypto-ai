import { INTERVAL_DURATION_MS } from '@/components/dashboard/lib/chartInterval'
import { BTC_PRICE_HISTORY_PATH } from '@/constants/apiUrls'
import { apiUrl } from '@/lib/apiConfig'
import { TIME_RANGE_LOOKBACK_MS } from '@/lib/timeRange'
import type {
  BtcPriceHistoryParams,
  BtcPriceHistoryPoint,
  BtcPriceHistoryResponse,
} from '@/types/btcPriceHistory'

export function btcPriceHistoryQueryKey(params: BtcPriceHistoryParams) {
  return ['btc-price-history', params.range, params.interval] as const
}

const MOCK_LATENCY_MS = 280
const MAX_POINTS = 500

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * Stand-in history for a frontend-only run. Returns chart-ready points already
 * bucketed by `interval` for the requested `range`.
 */
export async function simulateBtcPriceHistory(
  params: BtcPriceHistoryParams,
  endMs = Date.now(),
): Promise<BtcPriceHistoryResponse> {
  await delay(MOCK_LATENCY_MS)

  const lookbackMs = TIME_RANGE_LOOKBACK_MS[params.range]
  const intervalMs = INTERVAL_DURATION_MS[params.interval]
  const startMs = endMs - lookbackMs

  const idealCount = Math.floor(lookbackMs / intervalMs) + 1
  const stepMs =
    idealCount <= MAX_POINTS
      ? intervalMs
      : Math.ceil(lookbackMs / (MAX_POINTS - 1) / intervalMs) * intervalMs

  const points: BtcPriceHistoryPoint[] = []
  let close = 82_000

  for (
    let timestampMs = startMs, index = 0;
    timestampMs <= endMs;
    timestampMs += stepMs, index += 1
  ) {
    const open = close
    close = nextDeterministicPrice(open, index)
    points.push({
      timestamp: new Date(timestampMs).toISOString(),
      ...buildCandle(open, close, index),
    })
  }

  return {
    range: params.range,
    interval: params.interval,
    points,
  }
}

/**
 * Historical BTC OHLC candles from the data service (via gateway).
 *
 * With no backend configured the chart runs on simulated data so it still
 * works standalone. When a backend *is* configured a failed request throws
 * rather than quietly substituting invented candles.
 */
export async function fetchBtcPriceHistory(
  params: BtcPriceHistoryParams,
  endMs = Date.now(),
): Promise<BtcPriceHistoryResponse> {
  const url = apiUrl(BTC_PRICE_HISTORY_PATH)

  if (!url) {
    return simulateBtcPriceHistory(params, endMs)
  }

  const search = new URLSearchParams({
    range: params.range,
    interval: params.interval,
  })

  const response = await fetch(`${url}?${search}`, {
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) {
    throw new Error(`Price history request failed with ${response.status}`)
  }

  return (await response.json()) as BtcPriceHistoryResponse
}

/**
 * Slow trend plus per-bucket noise, both scaled to the price.
 *
 * Bucket-to-bucket moves have to stay a meaningful fraction of the window's
 * overall sweep, or every candle body collapses to a sub-pixel line against
 * the trend — which is not how a real series behaves.
 */
const TREND_RATIO = 0.0009
const NOISE_RATIO = 0.0022

function nextDeterministicPrice(previous: number, index: number) {
  const trend = Math.sin(index / 36) * previous * TREND_RATIO
  const noise =
    (Math.sin(index * 1.7) * 0.7 + Math.sin(index * 0.53) * 0.3) *
    previous *
    NOISE_RATIO

  return Math.max(1, previous + trend + noise)
}

/**
 * Wick the bucket out beyond its body, so candles carry the intra-bucket
 * range a close-only series throws away.
 *
 * The extent is a fraction of the price rather than a flat amount: a fixed
 * few dollars is invisible next to a multi-day trend, which is what makes
 * real candles readable at any zoom.
 */
const MIN_WICK_RATIO = 0.0015
const WICK_RATIO_SWING = 0.0015

function buildCandle(open: number, close: number, index: number) {
  const mid = (open + close) / 2
  const extent =
    mid * (MIN_WICK_RATIO + Math.abs(Math.sin(index / 5)) * WICK_RATIO_SWING)

  const upperWick = extent * (0.5 + Math.abs(Math.cos(index / 7)) * 0.5)
  const lowerWick = extent * (0.5 + Math.abs(Math.sin(index / 9)) * 0.5)

  return {
    open: roundCents(open),
    high: roundCents(Math.max(open, close) + upperWick),
    low: roundCents(Math.max(1, Math.min(open, close) - lowerWick)),
    close: roundCents(close),
  }
}

function roundCents(value: number) {
  return Math.round(value * 100) / 100
}
