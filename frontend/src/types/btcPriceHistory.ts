import type { ChartInterval } from '@/types/chart'
import type { TimeRange } from '@/types/preferences'

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
