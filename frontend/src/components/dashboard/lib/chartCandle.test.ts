import { describe, expect, it } from 'vitest'
import type { BtcPriceHistoryPoint } from '@/types/btcPriceHistory'
import {
  candleYDomain,
  mapHistoryPointsToChartCandles,
  Y_DOMAIN_PADDING_RATIO,
} from '@/components/dashboard/lib/chartCandle'

const SAMPLE_POINTS: BtcPriceHistoryPoint[] = [
  {
    timestamp: '2024-03-05T14:30:00.000Z',
    open: 64_000,
    high: 64_400,
    low: 63_900,
    close: 64_100.5,
  },
  {
    timestamp: '2024-03-06T09:00:00.000Z',
    open: 64_100.5,
    high: 64_500,
    low: 64_050,
    close: 64_250,
  },
]

describe('mapHistoryPointsToChartCandles', () => {
  it('maps every OHLC value through unchanged', () => {
    const [first] = mapHistoryPointsToChartCandles(SAMPLE_POINTS, '1h')

    expect(first.open).toBe(64_000)
    expect(first.high).toBe(64_400)
    expect(first.low).toBe(63_900)
    expect(first.close).toBe(64_100.5)
    expect(first.timeMs).toBe(Date.parse('2024-03-05T14:30:00.000Z'))
  })

  it('formats fine intervals with day and clock time', () => {
    const [point] = mapHistoryPointsToChartCandles(
      [{ timestamp: '2024-03-05T14:30:00.000Z', open: 1, high: 1, low: 1, close: 1 }],
      '1m',
    )

    expect(point.time).toBe('Mar 5 14:30')
  })

  it('formats hourly labels on the hour', () => {
    const [point] = mapHistoryPointsToChartCandles(
      [{ timestamp: '2024-03-05T14:30:00.000Z', open: 1, high: 1, low: 1, close: 1 }],
      '1h',
    )

    expect(point.time).toBe('Mar 5 14:00')
  })

  it('formats daily labels with weekday', () => {
    const [point] = mapHistoryPointsToChartCandles(
      [{ timestamp: '2024-03-05T14:30:00.000Z', open: 1, high: 1, low: 1, close: 1 }],
      '1d',
    )

    expect(point.time).toBe('Tue, Mar 5')
  })

  it('formats weekly labels as date only', () => {
    const [point] = mapHistoryPointsToChartCandles(
      [{ timestamp: '2024-03-05T14:30:00.000Z', open: 1, high: 1, low: 1, close: 1 }],
      '1w',
    )

    expect(point.time).toBe('Mar 5')
  })

  it('formats monthly labels as month and year', () => {
    const [point] = mapHistoryPointsToChartCandles(
      [{ timestamp: '2024-03-05T14:30:00.000Z', open: 1, high: 1, low: 1, close: 1 }],
      '1mo',
    )

    expect(point.time).toBe('Mar 2024')
  })

  it('formats yearly labels as the UTC year', () => {
    const [point] = mapHistoryPointsToChartCandles(
      [{ timestamp: '2024-03-05T14:30:00.000Z', open: 1, high: 1, low: 1, close: 1 }],
      '1y',
    )

    expect(point.time).toBe('2024')
  })

  it('returns an empty series for empty history', () => {
    expect(mapHistoryPointsToChartCandles([], '1h')).toEqual([])
  })
})

describe('candleYDomain', () => {
  function candles(...ranges: [number, number][]) {
    return ranges.map(([low, high]) => ({
      time: 't',
      timeMs: 0,
      open: low,
      high,
      low,
      close: high,
    }))
  }

  it('spans the wicks, not just the bodies', () => {
    const [min, max] = candleYDomain(candles([100, 200], [150, 260]))

    expect(min).toBeLessThan(100)
    expect(max).toBeGreaterThan(260)
  })

  it('pads proportionally to the span', () => {
    const [min, max] = candleYDomain(candles([100, 200]))

    expect(min).toBeCloseTo(100 - 100 * Y_DOMAIN_PADDING_RATIO)
    expect(max).toBeCloseTo(200 + 100 * Y_DOMAIN_PADDING_RATIO)
  })

  it('still produces a usable range for a flat series', () => {
    const [min, max] = candleYDomain(candles([64_000, 64_000]))

    expect(max).toBeGreaterThan(min)
  })

  it('falls back to a safe range when there are no candles', () => {
    expect(candleYDomain([])).toEqual([0, 1])
  })
})
