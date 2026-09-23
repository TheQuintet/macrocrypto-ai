import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { RegimeHistoryRowResponse } from '@/types/regime'

const WIRE_ROWS: RegimeHistoryRowResponse[] = [
  {
    id: 5,
    regime_type: 'rising_rates',
    start_date: '2024-03-01',
    end_date: null,
    performance: null,
  },
  {
    id: 4,
    regime_type: 'growth',
    start_date: '2023-08-01',
    end_date: '2024-02-29',
    performance: {
      avg_return: 28.4,
      max_drawdown: -11.2,
      volatility: 36.8,
      sharpe_ratio: 1.42,
      btc_price_start: 47_800,
      btc_price_end: 61_400,
    },
  },
]

function response(body: unknown, init: { ok?: boolean; status?: number } = {}) {
  return vi.fn().mockResolvedValue({
    ok: init.ok ?? true,
    status: init.status ?? 200,
    json: async () => body,
  })
}

async function loadApi() {
  return import('@/api/regimes/regimeHistory')
}

describe('fetchRegimeHistory without a backend', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', '')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('returns simulated rows, labelled as such, without any HTTP', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchRegimeHistory } = await loadApi()

    const history = await fetchRegimeHistory()

    expect(fetchSpy).not.toHaveBeenCalled()
    expect(history.source).toBe('simulated')
    expect(history.rows.length).toBeGreaterThan(0)
  })

  it('leaves exactly one simulated regime open', async () => {
    const { fetchRegimeHistory } = await loadApi()
    const { rows } = await fetchRegimeHistory()

    expect(rows.filter((row) => row.isCurrent)).toHaveLength(1)
  })

  it('gives every simulated regime a start date the timeline can read', async () => {
    const { fetchRegimeHistory } = await loadApi()
    const { rows } = await fetchRegimeHistory()

    for (const row of rows) {
      expect(Number.isNaN(Date.parse(row.startDate))).toBe(false)
    }
  })
})

describe('fetchRegimeHistory with a backend configured', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'http://localhost:8000')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('calls the gateway regime history endpoint', async () => {
    const fetchSpy = response(WIRE_ROWS)
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchRegimeHistory } = await loadApi()

    await fetchRegimeHistory()

    expect(fetchSpy).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/regimes',
      { headers: { Accept: 'application/json' } },
    )
  })

  it('treats a null end date as the regime still running', async () => {
    vi.stubGlobal('fetch', response(WIRE_ROWS))
    const { fetchRegimeHistory } = await loadApi()

    const { rows } = await fetchRegimeHistory()

    expect(rows[0].isCurrent).toBe(true)
    expect(rows[1].isCurrent).toBe(false)
  })

  it('maps the nested performance block and marks it live', async () => {
    vi.stubGlobal('fetch', response(WIRE_ROWS))
    const { fetchRegimeHistory } = await loadApi()

    const { source, rows } = await fetchRegimeHistory()

    expect(source).toBe('live')
    expect(rows[1].performance).toEqual({
      avgReturn: 28.4,
      maxDrawdown: -11.2,
      volatility: 36.8,
      sharpeRatio: 1.42,
      btcPriceStart: 47_800,
      btcPriceEnd: 61_400,
    })
  })

  it('keeps a regime with no performance rather than dropping it', async () => {
    vi.stubGlobal('fetch', response(WIRE_ROWS))
    const { fetchRegimeHistory } = await loadApi()

    const { rows } = await fetchRegimeHistory()

    expect(rows).toHaveLength(2)
    expect(rows[0].performance).toBeNull()
  })

  it('survives a payload that is not an array', async () => {
    vi.stubGlobal('fetch', response({ detail: 'unexpected' }))
    const { fetchRegimeHistory } = await loadApi()

    await expect(fetchRegimeHistory()).resolves.toEqual({
      source: 'live',
      rows: [],
    })
  })

  it('throws on a server error rather than substituting simulated data', async () => {
    vi.stubGlobal('fetch', response(null, { ok: false, status: 500 }))
    const { fetchRegimeHistory } = await loadApi()

    await expect(fetchRegimeHistory()).rejects.toThrow(/500/)
  })
})
