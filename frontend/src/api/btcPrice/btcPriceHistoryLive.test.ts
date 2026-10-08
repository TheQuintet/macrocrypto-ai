import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { BtcPriceHistoryResponse } from '@/types/btcPriceHistory'

const WIRE_RESPONSE: BtcPriceHistoryResponse = {
  range: '30d',
  interval: '1h',
  points: [
    {
      timestamp: '2024-06-01T12:00:00.000Z',
      open: 64_000,
      high: 64_500,
      low: 63_800,
      close: 64_200,
    },
  ],
}

function okResponse(body: unknown) {
  return vi.fn().mockResolvedValue({ ok: true, json: async () => body })
}

async function loadApi() {
  return import('@/api/btcPrice/btcPriceHistory')
}

describe('fetchBtcPriceHistory with a backend configured', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'http://localhost:8000')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('calls the gateway with dashboard time ranges including 1y', async () => {
    const fetchSpy = okResponse({ ...WIRE_RESPONSE, range: '1y', interval: '1w' })
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchBtcPriceHistory } = await loadApi()

    await fetchBtcPriceHistory({ range: '1y', interval: '1w' })

    expect(fetchSpy).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/btc/price/history?range=1y&interval=1w',
      { headers: { Accept: 'application/json' } },
    )
  })

  it('calls the gateway price history endpoint with range and interval', async () => {
    const fetchSpy = okResponse(WIRE_RESPONSE)
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchBtcPriceHistory } = await loadApi()

    await fetchBtcPriceHistory({ range: '30d', interval: '1h' })

    expect(fetchSpy).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/btc/price/history?range=30d&interval=1h',
      { headers: { Accept: 'application/json' } },
    )
  })

  it('returns the live payload without generating candles locally', async () => {
    vi.stubGlobal('fetch', okResponse(WIRE_RESPONSE))
    const { fetchBtcPriceHistory } = await loadApi()

    const history = await fetchBtcPriceHistory({ range: '30d', interval: '1h' })

    expect(history).toEqual(WIRE_RESPONSE)
  })

  it('throws on a server error rather than substituting simulated data', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: false, status: 503 }),
    )
    const { fetchBtcPriceHistory } = await loadApi()

    await expect(
      fetchBtcPriceHistory({ range: '90d', interval: '1d' }),
    ).rejects.toThrow('Price history request failed with 503')
  })
})

describe('fetchBtcPriceHistory with no backend configured', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('does not call fetch and uses simulated candles', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchBtcPriceHistory } = await loadApi()

    const pending = fetchBtcPriceHistory({ range: '30d', interval: '1h' })
    await vi.advanceTimersByTimeAsync(280)
    const history = await pending

    expect(fetchSpy).not.toHaveBeenCalled()
    expect(history.points.length).toBeGreaterThan(1)
  })
})
