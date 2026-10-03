import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  mapPredictionAccuracyPoints,
  predictionAccuracyPointsQueryKey,
  predictionAccuracyPointsSearchParams,
  simulatePredictionAccuracyPoints,
} from '@/api/predictions/predictionAccuracyPoints'
import {
  makePerformancePointResponse,
  makePerformancePointsResponse,
} from '@/api/predictions/predictionAccuracyPoints.testHelpers'
import {
  buildSimulatedPerformance,
  buildSimulatedPerformancePoints,
} from '@/api/predictions/simulatedPredictionAccuracy'
import type { PerformancePointsResponse } from '@/types/predictionAccuracy'

const FIXED_NOW_MS = Date.UTC(2026, 8, 14, 12, 0, 0)

/** Mean |predicted − actual| / actual, in percent — how the service scores MAPE. */
function pointsMape(response: PerformancePointsResponse) {
  const total = response.points.reduce(
    (sum, point) =>
      sum +
      Math.abs(point.predicted_price - point.actual_price) / point.actual_price,
    0,
  )
  return (total / response.points.length) * 100
}

describe('predictionAccuracyPointsQueryKey', () => {
  it('caches each horizon, window and model separately', () => {
    const key = predictionAccuracyPointsQueryKey({
      horizon: '24h',
      days: 30,
      modelName: 'prophet_fresh',
    })

    expect(key).toEqual([
      'btc-prediction-accuracy-points',
      '24h',
      30,
      'prophet_fresh',
    ])
    expect(
      predictionAccuracyPointsQueryKey({
        horizon: '24h',
        days: 30,
        modelName: 'xgboost_fresh',
      }),
    ).not.toEqual(key)
  })
})

describe('predictionAccuracyPointsSearchParams', () => {
  it('asks for one horizon and model over the window', () => {
    const params = predictionAccuracyPointsSearchParams({
      horizon: '7d',
      days: 30,
      modelName: 'prophet_fresh',
    })

    expect(params.toString()).toBe(
      'horizon=7d&days=30&model_name=prophet_fresh',
    )
  })

  it('leaves the model to the service when none is named', () => {
    const params = predictionAccuracyPointsSearchParams({
      horizon: '24h',
      days: 30,
    })

    expect(params.has('model_name')).toBe(false)
  })
})

describe('mapPredictionAccuracyPoints', () => {
  it('camel-cases the response', () => {
    expect(
      mapPredictionAccuracyPoints(makePerformancePointsResponse(), '24h'),
    ).toEqual({
      source: 'live',
      horizon: '24h',
      modelName: 'prophet_fresh',
      modelVersion: '1.0.0',
      periodDays: 30,
      points: [
        {
          time: '2026-09-14T06:00:00Z',
          timeMs: Date.UTC(2026, 8, 14, 6),
          predicted: 64_100.5,
          actual: 63_880.2,
          marketCondition: 'bull',
        },
      ],
    })
  })

  it('keeps a point the service did not classify, or labelled unknown', () => {
    const mapped = mapPredictionAccuracyPoints(
      makePerformancePointsResponse({
        model_version: null,
        points: [
          makePerformancePointResponse({ market_condition: null }),
          makePerformancePointResponse({ market_condition: 'sideways' }),
        ],
      }),
      '24h',
    )

    expect(mapped.modelVersion).toBeNull()
    expect(mapped.points.map((point) => point.marketCondition)).toEqual([
      null,
      null,
    ])
  })

  it('maps an empty window to no points rather than inventing any', () => {
    expect(
      mapPredictionAccuracyPoints(
        makePerformancePointsResponse({ points: [] }),
        '7d',
      ).points,
    ).toEqual([])
  })
})

describe('buildSimulatedPerformancePoints', () => {
  it('is deterministic for a moment in time', () => {
    const params = { horizon: '24h', days: 30 } as const

    expect(buildSimulatedPerformancePoints(params, FIXED_NOW_MS)).toEqual(
      buildSimulatedPerformancePoints(params, FIXED_NOW_MS),
    )
  })

  it('scores as many forecasts as the accuracy entry counts, oldest first', () => {
    for (const horizon of ['24h', '7d'] as const) {
      const params = { horizon, days: 30 }
      const points = buildSimulatedPerformancePoints(params, FIXED_NOW_MS)
      const entry = buildSimulatedPerformance(params, FIXED_NOW_MS).entries[0]
      const times = points.points.map((point) =>
        new Date(point.forecast_date).getTime(),
      )

      expect(points.points).toHaveLength(entry.samples)
      expect(times).toEqual([...times].sort((a, b) => a - b))
      expect(Math.max(...times)).toBeLessThanOrEqual(FIXED_NOW_MS)
    }
  })

  it('misses by about the average % miss the card reports', () => {
    for (const horizon of ['24h', '7d'] as const) {
      const params = { horizon, days: 30 }
      const best = buildSimulatedPerformance(params, FIXED_NOW_MS).entries[0]
      const points = buildSimulatedPerformancePoints(
        { ...params, modelName: best.model_name },
        FIXED_NOW_MS,
      )

      expect(pointsMape(points)).toBeCloseTo(best.metrics.mape!, 0)
    }
  })

  it('compares the model it was asked about', () => {
    const points = buildSimulatedPerformancePoints(
      { horizon: '24h', days: 30, modelName: 'xgboost_fresh' },
      FIXED_NOW_MS,
    )

    expect(points.model_name).toBe('xgboost_fresh')
  })
})

describe('simulatePredictionAccuracyPoints', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('resolves the comparison labelled as simulated', async () => {
    const pending = simulatePredictionAccuracyPoints(
      { horizon: '7d', days: 30, modelName: 'prophet_fresh' },
      FIXED_NOW_MS,
    )
    await vi.advanceTimersByTimeAsync(200)
    const comparison = await pending

    expect(comparison.source).toBe('simulated')
    expect(comparison.horizon).toBe('7d')
    expect(comparison.points).toHaveLength(30)
  })
})

describe('fetchPredictionAccuracyPoints with a backend configured', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'http://localhost:8000')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  async function loadApi() {
    return import('@/api/predictions/predictionAccuracyPoints')
  }

  it('calls the points endpoint for the graded model', async () => {
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => makePerformancePointsResponse(),
    })
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchPredictionAccuracyPoints } = await loadApi()

    const comparison = await fetchPredictionAccuracyPoints({
      horizon: '24h',
      days: 30,
      modelName: 'prophet_fresh',
    })

    expect(fetchSpy).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/performance/btc/points?horizon=24h&days=30&model_name=prophet_fresh',
      { headers: { Accept: 'application/json' } },
    )
    expect(comparison.source).toBe('live')
  })

  it('throws on a failed request instead of drawing simulated prices', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: false, status: 404 }),
    )
    const { fetchPredictionAccuracyPoints } = await loadApi()

    await expect(
      fetchPredictionAccuracyPoints({ horizon: '7d', days: 30 }),
    ).rejects.toThrow('Comparison request failed with 404')
  })
})
