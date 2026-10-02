import type {
  AccuracyThreshold,
  PerformanceEntryResponse,
  PerformanceResponse,
  PredictionAccuracy,
} from '@/types/predictionAccuracy'

/** One `PerformanceEntry` as the service serialises it. */
export function makePerformanceEntryResponse(
  overrides: Partial<PerformanceEntryResponse> = {},
): PerformanceEntryResponse {
  return {
    model_name: 'prophet_fresh',
    model_version: '1.0.0',
    horizon: '24h',
    samples: 720,
    metrics: {
      mae: 500,
      rmse: 700,
      mape: 1.2,
      directional_accuracy: 61.5,
    },
    market_breakdown: {
      bull: { mae: 450, rmse: 600, mape: 1, samples: 300 },
    },
    thresholds: [
      {
        metric: 'mae_pct',
        value: 1,
        threshold: 10,
        breached: false,
        breach_direction: 'above',
        consecutive_days: 0,
        warning: false,
      },
    ],
    recent_breach_count: 0,
    last_updated: '2026-09-14T11:00:00Z',
    warning: false,
    warning_count: 0,
    warning_threshold_days: 3,
    history: [
      {
        calculated_at: '2026-09-13T07:15:00Z',
        mae: 480,
        rmse: 690,
        mape: 1.1,
        directional_accuracy: 61.5,
        sample_size: 1,
      },
    ],
    ...overrides,
  }
}

/** A `GET /api/v1/performance/btc` body — the schema's own example. */
export function makePerformanceResponse(
  overrides: Partial<PerformanceResponse> = {},
): PerformanceResponse {
  return {
    time_period_days: 30,
    generated_at: '2026-09-14T12:00:00Z',
    entries: [makePerformanceEntryResponse()],
    warnings_count: 0,
    best_model: 'prophet_fresh',
    ...overrides,
  }
}

export function makeAccuracyThreshold(
  overrides: Partial<AccuracyThreshold> = {},
): AccuracyThreshold {
  return {
    metric: 'directional_accuracy',
    value: 61.5,
    threshold: 55,
    breached: false,
    breachDirection: 'below',
    consecutiveDays: 0,
    warning: false,
    ...overrides,
  }
}

/** A MAPE check the service has been warning about for four days. */
export function makeMapeWarning(
  overrides: Partial<AccuracyThreshold> = {},
): AccuracyThreshold {
  return makeAccuracyThreshold({
    metric: 'mape',
    value: 10.8,
    threshold: 10,
    breachDirection: 'above',
    breached: true,
    warning: true,
    consecutiveDays: 4,
    ...overrides,
  })
}

/**
 * A mapped entry in the shape the fetcher returns, for component specs.
 *
 * Filled the way the service fills it today: no directional figure, so the
 * headline is price accuracy, and %-of-price checks on MAE and MAPE.
 */
export function makePredictionAccuracy(
  overrides: Partial<PredictionAccuracy> = {},
): PredictionAccuracy {
  const dayMs = 24 * 60 * 60 * 1000
  const startMs = Date.UTC(2026, 8, 10, 6)

  return {
    source: 'simulated',
    horizon: '24h',
    modelName: 'prophet_fresh',
    modelVersion: '1.0.0',
    isBestModel: true,
    periodDays: 30,
    samples: 720,
    lastUpdated: '2026-09-14T06:00:00Z',
    metrics: {
      mae: 1_152.4,
      rmse: 1_555.7,
      mape: 1.8,
      directionalAccuracy: null,
    },
    marketBreakdown: [
      { condition: 'bull', mae: 979.5, mape: 1.53, samples: 252 },
      { condition: 'volatile', mae: 1_843.2, mape: 2.88, samples: 108 },
    ],
    thresholds: [
      makeAccuracyThreshold({
        metric: 'mae_pct',
        value: 1.8,
        threshold: 10,
        breachDirection: 'above',
      }),
      makeAccuracyThreshold({
        metric: 'mape',
        value: 1.8,
        threshold: 10,
        breachDirection: 'above',
      }),
    ],
    warning: false,
    warningCount: 0,
    warningThresholdDays: 3,
    history: Array.from({ length: 5 }, (_, index) => {
      const timeMs = startMs + index * dayMs
      return {
        time: new Date(timeMs).toISOString(),
        timeMs,
        mape: 1.8 + index * 0.1,
        directionalAccuracy: 60 + index,
        sampleSize: 24,
      }
    }),
    ...overrides,
  }
}
