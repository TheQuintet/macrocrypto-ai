import type { BtcPriceHistoryPoint } from '@/api/btcPriceHistory'
import type { ChartInterval } from '@/dashboard/chartInterval'

/** Recharts display point (label + close price). */
export type ChartPoint = {
  time: string
  price: number
}

/** Map API history points to chart series — formatting only, no aggregation. */
export function mapHistoryPointsToChartPoints(
  points: BtcPriceHistoryPoint[],
  interval: ChartInterval,
): ChartPoint[] {
  return points.map((point) => ({
    time: formatHistoryLabel(point.timestamp, interval),
    price: point.price,
  }))
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
