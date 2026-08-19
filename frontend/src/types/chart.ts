/** Candle / bucket size — independent from the time-range lookback window. */
export type ChartInterval = '1m' | '5m' | '1h' | '1d' | '1w' | '1y'

export type ChartType = 'line' | 'candles'

/**
 * One OHLC bucket, label already formatted for the axis.
 * The line chart plots `close`; the candlestick chart uses all four.
 */
export type ChartCandle = {
  time: string
  open: number
  high: number
  low: number
  close: number
}
