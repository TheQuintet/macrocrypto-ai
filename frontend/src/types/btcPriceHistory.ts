import type { ChartInterval } from '@/types/chart'
import type { TimeRange } from '@/types/preferences'

/**
 * Production-shaped history request.
 * Real gateway: GET /api/v1/btc/price/history?range=30d&interval=1d
 * (`range`: 24h | 7d | 30d | 90d | 1y | 5y; `interval`: 1m | 5m | 1h | 1d | 1w | 1y)
 */
export type BtcPriceHistoryParams = {
  range: TimeRange
  interval: ChartInterval
}

/**
 * Production-shaped history candle.
 * Mirrors a Binance kline as the service already reads it — see
 * `DailyCandle` in `services/data-service/app/services/history_service.py`.
 */
export type BtcPriceHistoryPoint = {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
}

export type BtcPriceHistoryResponse = {
  range: TimeRange
  interval: ChartInterval
  points: BtcPriceHistoryPoint[]
}
