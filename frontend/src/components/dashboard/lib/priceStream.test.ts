import { describe, expect, it } from 'vitest'
import {
  parsePriceStreamMessage,
  reconnectDelayMs,
  RECONNECT_BASE_DELAY_MS,
  RECONNECT_MAX_DELAY_MS,
} from '@/components/dashboard/lib/priceStream'

describe('reconnectDelayMs', () => {
  it('backs off exponentially from the base delay', () => {
    expect(reconnectDelayMs(1)).toBe(RECONNECT_BASE_DELAY_MS)
    expect(reconnectDelayMs(2)).toBe(RECONNECT_BASE_DELAY_MS * 2)
    expect(reconnectDelayMs(3)).toBe(RECONNECT_BASE_DELAY_MS * 4)
  })

  it('caps the delay so a long outage keeps retrying', () => {
    expect(reconnectDelayMs(20)).toBe(RECONNECT_MAX_DELAY_MS)
  })

  it('treats the first attempt as the base delay', () => {
    expect(reconnectDelayMs(0)).toBe(RECONNECT_BASE_DELAY_MS)
  })
})

describe('parsePriceStreamMessage', () => {
  it('maps a price frame to a snapshot', () => {
    const snapshot = parsePriceStreamMessage(
      JSON.stringify({
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
    )

    expect(snapshot?.currentPrice).toBe(64_213.5)
    expect(snapshot?.change7dPercent).toBe(4.58)
    expect(snapshot?.updatedAt).toBe('2024-06-15T12:00:00.000Z')
  })

  it('fills absent fields with null rather than undefined', () => {
    const snapshot = parsePriceStreamMessage(
      JSON.stringify({ current_price: 64_000 }),
    )

    expect(snapshot).toEqual({
      currentPrice: 64_000,
      change24h: null,
      change24hPercent: null,
      high24h: null,
      low24h: null,
      volume24h: null,
      change7d: null,
      change7dPercent: null,
      updatedAt: null,
    })
  })

  it('rejects malformed frames instead of throwing', () => {
    expect(parsePriceStreamMessage('not json')).toBeNull()
    expect(parsePriceStreamMessage('null')).toBeNull()
    expect(parsePriceStreamMessage('[]')).toBeNull()
    expect(parsePriceStreamMessage(JSON.stringify({ price: 1 }))).toBeNull()
  })

  it('drops non-numeric price values', () => {
    const snapshot = parsePriceStreamMessage(
      JSON.stringify({ current_price: 'expensive' }),
    )

    expect(snapshot?.currentPrice).toBeNull()
  })
})
