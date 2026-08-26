import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  btcPriceHistoryQueryKey,
  fetchBtcPriceHistory,
} from '@/api/btcPriceHistory'
import { INTERVAL_DURATION_MS } from '@/components/dashboard/lib/chartInterval'

const FIXED_END_MS = Date.UTC(2024, 5, 15, 12, 0, 0) // 2024-06-15T12:00:00.000Z

describe('btcPriceHistoryQueryKey', () => {
  it('keys history by range and interval', () => {
    expect(
      btcPriceHistoryQueryKey({ range: '30d', interval: '1h' }),
    ).toEqual(['btc-price-history', '30d', '1h'])
  })
})

describe('fetchBtcPriceHistory', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  async function fetchSettled(
    params: Parameters<typeof fetchBtcPriceHistory>[0],
  ) {
    const pending = fetchBtcPriceHistory(params, FIXED_END_MS)
    await vi.advanceTimersByTimeAsync(280)
    return pending
  }

  it('returns chart-ready points already bucketed by interval', async () => {
    const response = await fetchSettled({ range: '30d', interval: '1h' })

    expect(response.range).toBe('30d')
    expect(response.interval).toBe('1h')
    expect(response.points.length).toBeGreaterThan(1)

    for (const point of response.points) {
      expect(point.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T/)
      expect(point.close).toBeGreaterThan(0)
      expect(Number.isFinite(point.close)).toBe(true)
    }
  })

  it('spaces points by the requested interval when under the cap', async () => {
    const response = await fetchSettled({ range: '30d', interval: '1d' })
    const stepMs = INTERVAL_DURATION_MS['1d']

    expect(response.points.length).toBeLessThanOrEqual(500)

    for (let index = 1; index < response.points.length; index += 1) {
      const previous = Date.parse(response.points[index - 1].timestamp)
      const current = Date.parse(response.points[index].timestamp)
      expect(current - previous).toBe(stepMs)
    }
  })

  it('keeps lookback to the selected range', async () => {
    const response = await fetchSettled({ range: '30d', interval: '1d' })

    expect(response.points.length).toBeGreaterThan(1)

    const first = Date.parse(response.points[0].timestamp)
    const last = Date.parse(response.points.at(-1)!.timestamp)
    expect(last - first).toBeLessThanOrEqual(30 * 24 * 60 * 60_000)
    expect(last - first).toBeGreaterThan(20 * 24 * 60 * 60_000)
  })

  it('caps series length and widens the step when needed', async () => {
    const response = await fetchSettled({ range: '90d', interval: '1m' })
    const stepMs = INTERVAL_DURATION_MS['1m']

    expect(response.points.length).toBeLessThanOrEqual(500)
    expect(response.points.length).toBeGreaterThan(1)

    const gaps = response.points.slice(1).map((point, index) => {
      return (
        Date.parse(point.timestamp) -
        Date.parse(response.points[index].timestamp)
      )
    })

    expect(gaps.every((gap) => gap >= stepMs)).toBe(true)
    expect(gaps.every((gap) => gap % stepMs === 0)).toBe(true)
    expect(Math.max(...gaps)).toBeGreaterThan(stepMs)
  })

  it('returns candles whose wicks contain the body', async () => {
    const response = await fetchSettled({ range: '30d', interval: '1h' })

    for (const point of response.points) {
      expect(point.high).toBeGreaterThanOrEqual(Math.max(point.open, point.close))
      expect(point.low).toBeLessThanOrEqual(Math.min(point.open, point.close))
      expect(point.low).toBeGreaterThan(0)
    }
  })

  it('opens each candle at the previous close', async () => {
    const response = await fetchSettled({ range: '30d', interval: '1h' })

    for (let index = 1; index < response.points.length; index += 1) {
      expect(response.points[index].open).toBe(response.points[index - 1].close)
    }
  })

  it('ends near the provided end time', async () => {
    const response = await fetchSettled({ range: '30d', interval: '1d' })
    const last = Date.parse(response.points.at(-1)!.timestamp)

    expect(last).toBeLessThanOrEqual(FIXED_END_MS)
    expect(FIXED_END_MS - last).toBeLessThan(INTERVAL_DURATION_MS['1d'])
  })
})
