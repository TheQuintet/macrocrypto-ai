import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { RegimePerformanceRowResponse } from '@/types/regime'

const WIRE_ROWS: RegimePerformanceRowResponse[] = [
  {
    regime_id: 4,
    regime_type: 'growth',
    start_date: '2023-08-01',
    end_date: '2024-02-29',
    status: 'completed',
    performance: {
      avg_return: 28.4,
      max_drawdown: -11.2,
      volatility: 36.8,
      sharpe_ratio: 1.42,
      btc_price_start: 47_800,
      btc_price_end: 61_400,
    },
  },
  {
    regime_id: 5,
    regime_type: 'rising_rates',
    start_date: '2024-03-01',
    end_date: null,
    status: 'active',
    performance: {
      avg_return: -4.2,
      max_drawdown: -18.6,
      volatility: 41.3,
      sharpe_ratio: -0.21,
      btc_price_start: 61_400,
      btc_price_end: 58_820,
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
  return import('@/api/regimes/regimePerformance')
}

describe('fetchRegimePerformance without a backend', () => {
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
    const { fetchRegimePerformance } = await loadApi()

    const performance = await fetchRegimePerformance()

    expect(fetchSpy).not.toHaveBeenCalled()
    expect(performance.source).toBe('simulated')
    expect(performance.rows.length).toBeGreaterThan(0)
  })

  it('keeps the simulated returns consistent with each regime’s stance', async () => {
    const { fetchRegimePerformance } = await loadApi()
    const { rows } = await fetchRegimePerformance()

    const bullish = rows.filter((row) =>
      ['growth', 'falling_rates', 'low_inflation'].includes(row.regimeType),
    )
    const bearish = rows.filter((row) =>
      ['recession', 'high_inflation', 'rising_rates'].includes(row.regimeType),
    )

    expect(bullish.length).toBeGreaterThan(0)
    expect(bearish.length).toBeGreaterThan(0)
    for (const row of bullish) {
      expect(row.performance.avgReturn).toBeGreaterThan(0)
    }
    for (const row of bearish) {
      expect(row.performance.avgReturn).toBeLessThan(0)
    }
  })

  it('marks exactly one simulated regime as the current one', async () => {
    const { fetchRegimePerformance } = await loadApi()
    const { rows } = await fetchRegimePerformance()

    expect(rows.filter((row) => row.status === 'active')).toHaveLength(1)
    expect(rows.find((row) => row.status === 'active')?.endDate).toBeNull()
  })
})

describe('fetchRegimePerformance with a backend configured', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'http://localhost:8000')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('calls the gateway performance endpoint', async () => {
    const fetchSpy = response(WIRE_ROWS)
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchRegimePerformance } = await loadApi()

    await fetchRegimePerformance()

    expect(fetchSpy).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/regimes/performance',
      { headers: { Accept: 'application/json' } },
    )
  })

  it('maps the real payload and marks it live', async () => {
    vi.stubGlobal('fetch', response(WIRE_ROWS))
    const { fetchRegimePerformance } = await loadApi()

    const { source, rows } = await fetchRegimePerformance()

    expect(source).toBe('live')
    expect(rows[0]).toEqual({
      regimeId: 4,
      regimeType: 'growth',
      startDate: '2023-08-01',
      endDate: '2024-02-29',
      status: 'completed',
      performance: {
        avgReturn: 28.4,
        maxDrawdown: -11.2,
        volatility: 36.8,
        sharpeRatio: 1.42,
        btcPriceStart: 47_800,
        btcPriceEnd: 61_400,
      },
    })
  })

  it('treats an unknown status as completed rather than as current', async () => {
    vi.stubGlobal(
      'fetch',
      response([{ ...WIRE_ROWS[0], status: 'superseded' }]),
    )
    const { fetchRegimePerformance } = await loadApi()

    expect((await fetchRegimePerformance()).rows[0].status).toBe('completed')
  })

  it('carries a missing metric through as null instead of zero', async () => {
    vi.stubGlobal(
      'fetch',
      response([
        {
          ...WIRE_ROWS[0],
          performance: { ...WIRE_ROWS[0].performance, sharpe_ratio: null },
        },
      ]),
    )
    const { fetchRegimePerformance } = await loadApi()

    const { rows } = await fetchRegimePerformance()

    expect(rows[0].performance.sharpeRatio).toBeNull()
    expect(rows[0].performance.avgReturn).toBe(28.4)
  })

  it('survives a payload that is not an array', async () => {
    vi.stubGlobal('fetch', response({ detail: 'unexpected' }))
    const { fetchRegimePerformance } = await loadApi()

    await expect(fetchRegimePerformance()).resolves.toEqual({
      source: 'live',
      rows: [],
    })
  })

  it('throws on a server error rather than substituting simulated data', async () => {
    vi.stubGlobal('fetch', response(null, { ok: false, status: 500 }))
    const { fetchRegimePerformance } = await loadApi()

    await expect(fetchRegimePerformance()).rejects.toThrow(/500/)
  })
})
