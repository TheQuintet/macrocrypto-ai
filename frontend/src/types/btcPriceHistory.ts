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
