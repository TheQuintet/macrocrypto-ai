/** Candle / bucket size — independent from the time-range lookback window. */
export type ChartInterval = '1m' | '5m' | '1h' | '1d' | '1w' | '1y'

export type ChartType = 'line' | 'bar'

/** Recharts display point (label + close price). */
export type ChartPoint = {
  time: string
  price: number
}
