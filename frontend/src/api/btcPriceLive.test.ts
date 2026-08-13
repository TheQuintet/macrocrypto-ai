import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { BtcPriceSnapshotResponse } from '@/types/btcPrice'

/** A real `GET /api/v1/btc/price` body, as `PriceResponse` serialises it. */
const WIRE_RESPONSE: BtcPriceSnapshotResponse = {
  current_price: 64_213.5,
  change_24h: 1_113.5,
  change_24h_percent: 1.76,
  high_24h: 64_993.5,
  low_24h: 63_573.5,
  volume_24h: 24_180.42,
  change_7d: 2_813.5,
  change_7d_percent: 4.58,
  updated_at: '2024-06-15T12:00:00.000Z',
}

function okResponse(body: unknown) {
  return vi.fn().mockResolvedValue({ ok: true, json: async () => body })
}

async function loadApi() {
  return import('@/api/btcPrice')
}

describe('fetchBtcPriceSnapshot with a backend configured', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8001')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('calls the data service price endpoint', async () => {
    const fetchSpy = okResponse(WIRE_RESPONSE)
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchBtcPriceSnapshot } = await loadApi()

    await fetchBtcPriceSnapshot()

    expect(fetchSpy).toHaveBeenCalledWith(
      'http://localhost:8001/api/v1/btc/price',
      { headers: { Accept: 'application/json' } },
    )
  })

  it('maps the real payload and marks it live', async () => {
    vi.stubGlobal('fetch', okResponse(WIRE_RESPONSE))
    const { fetchBtcPriceSnapshot } = await loadApi()

    const snapshot = await fetchBtcPriceSnapshot()

    expect(snapshot.source).toBe('live')
    expect(snapshot.currentPrice).toBe(64_213.5)
    expect(snapshot.change24hPercent).toBe(1.76)
    expect(snapshot.change7dPercent).toBe(4.58)
    expect(snapshot.volume24h).toBe(24_180.42)
    expect(snapshot.updatedAt).toBe('2024-06-15T12:00:00.000Z')
  })

  it('keeps the nulls the service sends before its first tick', async () => {
    vi.stubGlobal(
      'fetch',
      okResponse({ ...WIRE_RESPONSE, current_price: null, change_7d: null }),
    )
    const { fetchBtcPriceSnapshot } = await loadApi()

    const snapshot = await fetchBtcPriceSnapshot()

    expect(snapshot.currentPrice).toBeNull()
    expect(snapshot.change7d).toBeNull()
  })

  it('throws instead of substituting fake prices when the service fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503 }))
    const { fetchBtcPriceSnapshot } = await loadApi()

    await expect(fetchBtcPriceSnapshot()).rejects.toThrow(/503/)
  })

  it('propagates a network failure to the error state', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
    const { fetchBtcPriceSnapshot } = await loadApi()

    await expect(fetchBtcPriceSnapshot()).rejects.toThrow('offline')
  })

  it('does not double up slashes on a trailing-slash base URL', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8001/')
    vi.resetModules()
    const fetchSpy = okResponse(WIRE_RESPONSE)
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchBtcPriceSnapshot } = await loadApi()

    await fetchBtcPriceSnapshot()

    expect(fetchSpy).toHaveBeenCalledWith(
      'http://localhost:8001/api/v1/btc/price',
      expect.anything(),
    )
  })
})

describe('fetchBtcPriceSnapshot with no backend configured', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('falls back to simulated data and labels it as such', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchBtcPriceSnapshot } = await loadApi()

    const snapshot = await fetchBtcPriceSnapshot(Date.UTC(2024, 5, 15, 12))

    expect(fetchSpy).not.toHaveBeenCalled()
    expect(snapshot.source).toBe('simulated')
    expect(snapshot.currentPrice).toBeGreaterThan(0)
  })
})
