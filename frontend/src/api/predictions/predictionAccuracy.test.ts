import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  mapPredictionAccuracy,
  pickAccuracyEntry,
  predictionAccuracyQueryKey,
  predictionAccuracySearchParams,
  simulatePredictionAccuracy,
} from '@/api/predictions/predictionAccuracy'
import {
  makePerformanceEntryResponse,
  makePerformanceResponse,
} from '@/api/predictions/predictionAccuracy.testHelpers'
import { buildSimulatedPerformance } from '@/api/predictions/simulatedPredictionAccuracy'

const FIXED_NOW_MS = Date.UTC(2026, 8, 14, 12, 0, 0)

describe('predictionAccuracyQueryKey', () => {
  it('caches each horizon and window separately', () => {
    expect(predictionAccuracyQueryKey({ horizon: '24h', days: 30 })).toEqual([
      'btc-prediction-accuracy',
      '24h',
      30,
    ])
    expect(
      predictionAccuracyQueryKey({ horizon: '7d', days: 30 }),
    ).not.toEqual(predictionAccuracyQueryKey({ horizon: '24h', days: 30 }))
  })
})

describe('predictionAccuracySearchParams', () => {
  it('asks for one horizon over the window, with its history series', () => {
    const params = predictionAccuracySearchParams({ horizon: '7d', days: 30 })

    expect(params.get('horizon')).toBe('7d')
    expect(params.get('days')).toBe('30')
    expect(params.get('include_history')).toBe('true')
    expect(params.get('history_limit')).toBe('30')
  })

  it("caps the history at the service's limit on a long window", () => {
    const params = predictionAccuracySearchParams({ horizon: '24h', days: 365 })

    expect(params.get('days')).toBe('365')
    expect(params.get('history_limit')).toBe('90')
  })
})

describe('pickAccuracyEntry', () => {
  it("prefers the service's best model", () => {
    const response = makePerformanceResponse({
      best_model: 'xgboost_fresh',
      entries: [
        makePerformanceEntryResponse({ model_name: 'prophet_fresh' }),
        makePerformanceEntryResponse({ model_name: 'xgboost_fresh' }),
      ],
    })

    expect(pickAccuracyEntry(response, '24h')?.model_name).toBe(
      'xgboost_fresh',
    )
  })

  it('falls back to the lowest MAPE when the best model has no entry there', () => {
    const response = makePerformanceResponse({
      best_model: 'prophet_fresh',
      entries: [
        makePerformanceEntryResponse({ model_name: 'prophet_fresh' }),
        makePerformanceEntryResponse({
          model_name: 'xgboost_fresh',
          horizon: '7d',
          metrics: { mae: 1, rmse: 1, mape: 6, directional_accuracy: null },
        }),
        makePerformanceEntryResponse({
          model_name: 'lightgbm_fresh',
          horizon: '7d',
          metrics: { mae: 1, rmse: 1, mape: 4, directional_accuracy: null },
        }),
      ],
    })

    expect(pickAccuracyEntry(response, '7d')?.model_name).toBe(
      'lightgbm_fresh',
    )
  })

  it('returns null when nothing has been scored for the horizon', () => {
    expect(pickAccuracyEntry(makePerformanceResponse(), '7d')).toBeNull()
  })
})

describe('mapPredictionAccuracy', () => {
  it('camel-cases the chosen entry', () => {
    expect(mapPredictionAccuracy(makePerformanceResponse(), '24h')).toEqual({
      source: 'live',
      horizon: '24h',
      modelName: 'prophet_fresh',
      modelVersion: '1.0.0',
      isBestModel: true,
      periodDays: 30,
      samples: 720,
      lastUpdated: '2026-09-14T11:00:00Z',
      metrics: {
        mae: 500,
        rmse: 700,
        mape: 1.2,
        directionalAccuracy: 61.5,
      },
      marketBreakdown: [{ condition: 'bull', mae: 450, mape: 1, samples: 300 }],
      thresholds: [
        {
          metric: 'mae_pct',
          value: 1,
          threshold: 10,
          breached: false,
          breachDirection: 'above',
          consecutiveDays: 0,
          warning: false,
        },
      ],
      warning: false,
      warningCount: 0,
      warningThresholdDays: 3,
      history: [
        {
          time: '2026-09-13T07:15:00Z',
          timeMs: Date.UTC(2026, 8, 13, 7, 15),
          mape: 1.1,
          directionalAccuracy: 61.5,
          sampleSize: 1,
        },
      ],
    })
  })

  it('orders the market breakdown and drops buckets it does not know', () => {
    const accuracy = mapPredictionAccuracy(
      makePerformanceResponse({
        entries: [
          makePerformanceEntryResponse({
            market_breakdown: {
              neutral: { mae: 1, rmse: 1, mape: 1, samples: 1 },
              sideways: { mae: 1, rmse: 1, mape: 1, samples: 1 },
              bull: { mae: 1, rmse: 1, mape: 1, samples: 1 },
            },
          }),
        ],
      }),
      '24h',
    )

    expect(accuracy?.marketBreakdown.map((row) => row.condition)).toEqual([
      'bull',
      'neutral',
    ])
  })

  it('marks an entry that is not the overall best model', () => {
    const accuracy = mapPredictionAccuracy(
      makePerformanceResponse({ best_model: 'xgboost_incremental' }),
      '24h',
    )

    expect(accuracy?.isBestModel).toBe(false)
  })

  it('returns null rather than inventing an entry for an empty horizon', () => {
    expect(
      mapPredictionAccuracy(makePerformanceResponse({ entries: [] }), '24h'),
    ).toBeNull()
  })
})

describe('buildSimulatedPerformance', () => {
  it('is deterministic for a moment in time', () => {
    const params = { horizon: '24h', days: 30 } as const

    expect(buildSimulatedPerformance(params, FIXED_NOW_MS)).toEqual(
      buildSimulatedPerformance(params, FIXED_NOW_MS),
    )
  })

  it('returns entries for the requested horizon only, with a full history', () => {
    const response = buildSimulatedPerformance(
      { horizon: '7d', days: 30 },
      FIXED_NOW_MS,
    )

    expect(response.entries.length).toBeGreaterThan(0)
    for (const entry of response.entries) {
      expect(entry.horizon).toBe('7d')
      expect(entry.history).toHaveLength(30)
    }
  })

  it('keeps the 24h models healthy', () => {
    const response = buildSimulatedPerformance(
      { horizon: '24h', days: 30 },
      FIXED_NOW_MS,
    )

    expect(response.warnings_count).toBe(0)
  })

  it('fills entries the way the service does today, with no direction figure', () => {
    const response = buildSimulatedPerformance(
      { horizon: '24h', days: 30 },
      FIXED_NOW_MS,
    )

    for (const entry of response.entries) {
      expect(entry.metrics.directional_accuracy).toBeNull()
      expect(entry.thresholds.map((threshold) => threshold.metric)).toEqual([
        'mae_pct',
        'rmse_pct',
        'mape',
      ])
    }
  })

  it('shows the warning path on 7d, where the average miss tops 10%', () => {
    const response = buildSimulatedPerformance(
      { horizon: '7d', days: 30 },
      FIXED_NOW_MS,
    )
    const best = response.entries.find(
      (entry) => entry.model_name === response.best_model,
    )!
    const mape = best.thresholds.find(
      (threshold) => threshold.metric === 'mape',
    )!

    expect(best.warning).toBe(true)
    expect(best.warning_count).toBe(
      best.thresholds.filter((threshold) => threshold.warning).length,
    )
    expect(mape.breached).toBe(true)
    expect(mape.consecutive_days).toBeGreaterThanOrEqual(
      best.warning_threshold_days,
    )
  })

  it('never scores a history point in the future', () => {
    const response = buildSimulatedPerformance(
      { horizon: '24h', days: 30 },
      FIXED_NOW_MS,
    )

    for (const point of response.entries[0].history) {
      expect(new Date(point.calculated_at).getTime()).toBeLessThanOrEqual(
        FIXED_NOW_MS,
      )
    }
  })
})

describe('simulatePredictionAccuracy', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('resolves the best entry labelled as simulated', async () => {
    const pending = simulatePredictionAccuracy(
      { horizon: '24h', days: 30 },
      FIXED_NOW_MS,
    )
    await vi.advanceTimersByTimeAsync(200)
    const accuracy = await pending

    expect(accuracy?.source).toBe('simulated')
    expect(accuracy?.horizon).toBe('24h')
    expect(accuracy?.isBestModel).toBe(true)
  })
})
