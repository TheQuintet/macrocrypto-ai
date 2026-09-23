import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { SimilarPeriodsApiResponse } from '@/types/regime'

const WIRE: SimilarPeriodsApiResponse = {
  method: 'normalized Euclidean distance',
  period_count: 1,
  current_conditions: { cpi: 3.1, federal_funds_rate: 5.25 },
  similar_periods: [
    {
      period_start: '2018-06-01',
      period_end: '2019-01-31',
      distance: 0.18,
      similarity_score: 88.4,
      reason: 'Policy rate near the top of its cycle.',
      matching_indicators: [
        { indicator: 'federal_funds_rate', normalized_difference: 0.06 },
      ],
      macro_conditions: { cpi: 2.9, federal_funds_rate: 5.0 },
      btc_performance: {
        price_start: 7_480,
        price_end: 3_690,
        return_percent: -50.7,
        observations: 245,
      },
    },
  ],
}

function response(body: unknown, init: { ok?: boolean; status?: number } = {}) {
  return vi.fn().mockResolvedValue({
    ok: init.ok ?? true,
    status: init.status ?? 200,
    json: async () => body,
  })
}

async function loadApi() {
  return import('@/api/regimes/similarPeriods')
}

describe('fetchSimilarPeriods without a backend', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', '')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('returns simulated matches, labelled as such, without any HTTP', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchSimilarPeriods } = await loadApi()

    const result = await fetchSimilarPeriods()

    expect(fetchSpy).not.toHaveBeenCalled()
    expect(result.source).toBe('simulated')
    expect(result.periods.length).toBeGreaterThan(0)
  })

  it('orders simulated matches strongest first, as the endpoint does', async () => {
    const { fetchSimilarPeriods } = await loadApi()
    const { periods } = await fetchSimilarPeriods()
    const scores = periods.map((period) => period.similarityScore)

    expect([...scores].sort((a, b) => b - a)).toEqual(scores)
  })

  it('includes a match with no BTC history, which the endpoint can return', async () => {
    const { fetchSimilarPeriods } = await loadApi()
    const { periods } = await fetchSimilarPeriods()

    expect(periods.some((period) => period.btcPerformance === null)).toBe(true)
  })
})

describe('fetchSimilarPeriods with a backend configured', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'http://localhost:8000')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('asks for a limit the endpoint accepts', async () => {
    // `limit` is constrained to 3-5; anything else is a 422.
    const fetchSpy = response(WIRE)
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchSimilarPeriods, SIMILAR_PERIODS_LIMIT } = await loadApi()

    await fetchSimilarPeriods()

    expect(SIMILAR_PERIODS_LIMIT).toBeGreaterThanOrEqual(3)
    expect(SIMILAR_PERIODS_LIMIT).toBeLessThanOrEqual(5)
    expect(fetchSpy).toHaveBeenCalledWith(
      `http://localhost:8000/api/v1/regimes/history/similar-periods?limit=${SIMILAR_PERIODS_LIMIT}`,
      { headers: { Accept: 'application/json' } },
    )
  })

  it('maps the real payload and marks it live', async () => {
    vi.stubGlobal('fetch', response(WIRE))
    const { fetchSimilarPeriods } = await loadApi()

    const result = await fetchSimilarPeriods()

    expect(result.source).toBe('live')
    expect(result.method).toBe('normalized Euclidean distance')
    expect(result.currentConditions).toEqual({
      cpi: 3.1,
      federal_funds_rate: 5.25,
    })
    expect(result.periods[0]).toMatchObject({
      periodStart: '2018-06-01',
      periodEnd: '2019-01-31',
      similarityScore: 88.4,
      reason: 'Policy rate near the top of its cycle.',
      btcPerformance: {
        priceStart: 7_480,
        priceEnd: 3_690,
        returnPercent: -50.7,
        observations: 245,
      },
    })
  })

  it('keys a match by its window, since the service sends no id', async () => {
    vi.stubGlobal('fetch', response(WIRE))
    const { fetchSimilarPeriods } = await loadApi()

    const { periods } = await fetchSimilarPeriods()

    expect(periods[0].id).toBe('2018-06-01_2019-01-31')
  })

  it('keeps a match whose BTC history does not reach back far enough', async () => {
    vi.stubGlobal(
      'fetch',
      response({
        ...WIRE,
        similar_periods: [
          { ...WIRE.similar_periods[0], btc_performance: null },
        ],
      }),
    )
    const { fetchSimilarPeriods } = await loadApi()

    const { periods } = await fetchSimilarPeriods()

    expect(periods).toHaveLength(1)
    expect(periods[0].btcPerformance).toBeNull()
  })

  it('survives a payload with no matches and a message instead', async () => {
    vi.stubGlobal(
      'fetch',
      response({
        method: 'n/a',
        period_count: 0,
        current_conditions: {},
        similar_periods: [],
        message: 'Not enough indicator history',
      }),
    )
    const { fetchSimilarPeriods } = await loadApi()

    const result = await fetchSimilarPeriods()

    expect(result.periods).toEqual([])
    expect(result.message).toBe('Not enough indicator history')
  })

  it('throws on a server error rather than substituting simulated data', async () => {
    vi.stubGlobal('fetch', response(null, { ok: false, status: 500 }))
    const { fetchSimilarPeriods } = await loadApi()

    await expect(fetchSimilarPeriods()).rejects.toThrow(/500/)
  })
})
