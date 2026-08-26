/** Candle / bucket size for BTC history. */
export type ChartInterval = '1m' | '5m' | '1h' | '1d' | '1w' | '1mo' | '1y'

/** Candle sizes the chart can switch between. */
export type CandleInterval = Extract<ChartInterval, '1d' | '1w'>

/** Last macro print at or before a candle, plus the series indexed to 100. */
export type AsOfIndicatorPrint = {
  value: number
  indexed: number
  /** Print-over-print change of the as-of observation. */
  changePercent: number | null
}

/**
 * One OHLC bucket, label already formatted for the axis.
 * `asOfIndicators` is set when the plot is linked to macro history.
 */
export type ChartCandle = {
  time: string
  timeMs: number
  open: number
  high: number
  low: number
  close: number
  asOfIndicators?: Record<string, AsOfIndicatorPrint>
}
