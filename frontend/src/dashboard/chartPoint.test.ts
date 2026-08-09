import { describe, expect, it } from 'vitest'
import type { BtcPriceHistoryPoint } from '@/api/btc-price-history'
import { mapHistoryPointsToChartPoints } from '@/dashboard/chart-point'

const SAMPLE_POINTS: BtcPriceHistoryPoint[] = [
  { timestamp: '2024-03-05T14:30:00.000Z', price: 64_100.5 },
  { timestamp: '2024-03-06T09:00:00.000Z', price: 64_250 },
]

describe('mapHistoryPointsToChartPoints', () => {
  it('maps price through unchanged', () => {
    const chartPoints = mapHistoryPointsToChartPoints(SAMPLE_POINTS, '1h')

    expect(chartPoints.map((point) => point.price)).toEqual([
      64_100.5, 64_250,
    ])
  })

  it('formats fine intervals with day and clock time', () => {
    const [point] = mapHistoryPointsToChartPoints(
      [{ timestamp: '2024-03-05T14:30:00.000Z', price: 1 }],
      '1m',
    )

    expect(point.time).toBe('Mar 5 14:30')
  })

  it('formats hourly labels on the hour', () => {
    const [point] = mapHistoryPointsToChartPoints(
      [{ timestamp: '2024-03-05T14:30:00.000Z', price: 1 }],
      '1h',
    )

    expect(point.time).toBe('Mar 5 14:00')
  })

  it('formats daily labels with weekday', () => {
    const [point] = mapHistoryPointsToChartPoints(
      [{ timestamp: '2024-03-05T14:30:00.000Z', price: 1 }],
      '1d',
    )

    expect(point.time).toBe('Tue, Mar 5')
  })

  it('formats weekly labels as date only', () => {
    const [point] = mapHistoryPointsToChartPoints(
      [{ timestamp: '2024-03-05T14:30:00.000Z', price: 1 }],
      '1w',
    )

    expect(point.time).toBe('Mar 5')
  })

  it('formats yearly labels as the UTC year', () => {
    const [point] = mapHistoryPointsToChartPoints(
      [{ timestamp: '2024-03-05T14:30:00.000Z', price: 1 }],
      '1y',
    )

    expect(point.time).toBe('2024')
  })

  it('returns an empty series for empty history', () => {
    expect(mapHistoryPointsToChartPoints([], '1h')).toEqual([])
  })
})
