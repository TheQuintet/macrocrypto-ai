import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  btcPriceSnapshotQueryKey,
  buildMockBtcPriceSnapshot,
  fetchBtcPriceSnapshot,
  mapBtcPriceSnapshot,
  mockBtcPriceAt,
  PRICE_SNAPSHOT_TICK_MS,
} from '@/api/btcPrice/btcPrice'

const FIXED_NOW_MS = Date.UTC(2024, 5, 15, 12, 0, 0) // 2024-06-15T12:00:00.000Z

describe('btcPriceSnapshotQueryKey', () => {
  it('keys the single current-price snapshot', () => {
    expect(btcPriceSnapshotQueryKey()).toEqual(['btc-price-snapshot'])
  })
})

describe('mapBtcPriceSnapshot', () => {
  it('camel-cases the service payload', () => {
    expect(
      mapBtcPriceSnapshot({
        current_price: 64_213.5,
        change_24h: 1_113.5,
        change_24h_percent: 1.76,
        high_24h: 64_993.5,
        low_24h: 63_573.5,
        volume_24h: 24_180.42,
        change_7d: 2_813.5,
        change_7d_percent: 4.58,
        updated_at: '2024-06-15T12:00:00.000Z',
      }),
    ).toEqual({
      source: 'live',
      currentPrice: 64_213.5,
      change24h: 1_113.5,
      change24hPercent: 1.76,
      high24h: 64_993.5,
      low24h: 63_573.5,
      volume24h: 24_180.42,
      change7d: 2_813.5,
      change7dPercent: 4.58,
      updatedAt: '2024-06-15T12:00:00.000Z',
    })
  })

  it('preserves the nulls the service sends before its first tick', () => {
    const snapshot = mapBtcPriceSnapshot({
      current_price: null,
      change_24h: null,
      change_24h_percent: null,
      high_24h: null,
      low_24h: null,
      volume_24h: null,
      change_7d: null,
      change_7d_percent: null,
      updated_at: null,
    })

    expect(snapshot.currentPrice).toBeNull()
    expect(snapshot.change7dPercent).toBeNull()
  })
})

describe('mockBtcPriceAt', () => {
  it('is deterministic for a moment in time', () => {
    expect(mockBtcPriceAt(FIXED_NOW_MS)).toBe(mockBtcPriceAt(FIXED_NOW_MS))
  })

  it('holds steady within a snapshot tick and moves across ticks', () => {
    const sameTick = mockBtcPriceAt(FIXED_NOW_MS + PRICE_SNAPSHOT_TICK_MS - 1)
    const nextTick = mockBtcPriceAt(FIXED_NOW_MS + PRICE_SNAPSHOT_TICK_MS)

    expect(sameTick).toBe(mockBtcPriceAt(FIXED_NOW_MS))
    expect(nextTick).not.toBe(sameTick)
  })

  it('produces moves over the 1% flash threshold somewhere in a run', () => {
    const prices = Array.from({ length: 40 }, (_, tick) =>
      mockBtcPriceAt(FIXED_NOW_MS + tick * PRICE_SNAPSHOT_TICK_MS),
    )

    const biggestMovePercent = Math.max(
      ...prices
        .slice(1)
        .map((price, index) =>
          Math.abs(((price - prices[index]) / prices[index]) * 100),
        ),
    )

    expect(biggestMovePercent).toBeGreaterThan(1)
  })
})

describe('buildMockBtcPriceSnapshot', () => {
  it('derives both change windows from the current price', () => {
    const snapshot = buildMockBtcPriceSnapshot(FIXED_NOW_MS)

    expect(snapshot.current_price).toBe(mockBtcPriceAt(FIXED_NOW_MS))
    expect(snapshot.change_24h).not.toBeNull()
    expect(snapshot.change_24h_percent).not.toBeNull()
    expect(snapshot.change_7d).not.toBeNull()
    expect(snapshot.change_7d_percent).not.toBeNull()
    expect(snapshot.updated_at).toBe(new Date(FIXED_NOW_MS).toISOString())
  })

  it('keeps the 24h high above the low', () => {
    const snapshot = buildMockBtcPriceSnapshot(FIXED_NOW_MS)

    expect(snapshot.high_24h!).toBeGreaterThan(snapshot.current_price!)
    expect(snapshot.low_24h!).toBeLessThan(snapshot.current_price!)
  })
})

describe('fetchBtcPriceSnapshot', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('resolves a mapped snapshot for the requested moment', async () => {
    const pending = fetchBtcPriceSnapshot(FIXED_NOW_MS)
    await vi.advanceTimersByTimeAsync(180)
    const snapshot = await pending

    expect(snapshot.currentPrice).toBe(mockBtcPriceAt(FIXED_NOW_MS))
    expect(snapshot.updatedAt).toBe(new Date(FIXED_NOW_MS).toISOString())
  })
})
