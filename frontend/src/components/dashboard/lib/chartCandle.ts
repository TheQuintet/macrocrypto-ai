import type { BtcPriceHistoryPoint } from '@/types/btcPriceHistory'
import type { ChartCandle, ChartInterval } from '@/types/chart'

/** Map API history candles to chart series — formatting only, no aggregation. */
export function mapHistoryPointsToChartCandles(
  points: BtcPriceHistoryPoint[],
  interval: ChartInterval,
): ChartCandle[] {
  return points.map((point) => ({
    time: formatHistoryLabel(point.timestamp, interval),
    open: point.open,
    high: point.high,
    low: point.low,
    close: point.close,
  }))
}

/** Breathing room above and below the extremes, as a share of the span. */
export const Y_DOMAIN_PADDING_RATIO = 0.06

/**
 * Price range to scale the Y axis to.
 *
 * Spans the wicks rather than the closes so candles never clip, and is meant
 * to be given the *visible* candles: scaling to the whole series while the
 * X axis shows a window squeezes those candles into a sliver of the plot.
 */
export function candleYDomain(candles: ChartCandle[]): [number, number] {
  if (candles.length === 0) {
    return [0, 1]
  }

  let min = candles[0].low
  let max = candles[0].high
  for (const candle of candles) {
    min = Math.min(min, candle.low)
    max = Math.max(max, candle.high)
  }

  const span = max - min
  const padding = span > 0 ? span * Y_DOMAIN_PADDING_RATIO : Math.max(1, max * 0.001)

  return [min - padding, max + padding]
}

function formatHistoryLabel(timestamp: string, interval: ChartInterval) {
  const date = new Date(timestamp)
  const hh = String(date.getUTCHours()).padStart(2, '0')
  const mm = String(date.getUTCMinutes()).padStart(2, '0')
  const day = formatUtcDay(date)

  switch (interval) {
    case '1m':
      return `${day} ${hh}:${mm}`
    case '5m':
      return `${day} ${hh}:${mm}`
    case '1h':
      return `${day} ${hh}:00`
    case '1d':
      return date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        timeZone: 'UTC',
      })
    case '1w':
      return day
    case '1y':
      return String(date.getUTCFullYear())
  }
}

function formatUtcDay(date: Date) {
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  })
}
