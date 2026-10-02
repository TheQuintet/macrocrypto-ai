import type {
  PerformancePointResponse,
  PerformancePointsResponse,
  PredictionAccuracyPoints,
} from '@/types/predictionAccuracy'

/** One scored forecast as the service serialises it. */
export function makePerformancePointResponse(
  overrides: Partial<PerformancePointResponse> = {},
): PerformancePointResponse {
  return {
    forecast_date: '2026-09-14T06:00:00Z',
    predicted_price: 64_100.5,
    actual_price: 63_880.2,
    market_condition: 'bull',
    ...overrides,
  }
}

/** A `GET /api/v1/performance/btc/points` body — the contract's example. */
export function makePerformancePointsResponse(
  overrides: Partial<PerformancePointsResponse> = {},
): PerformancePointsResponse {
  return {
    horizon: '24h',
    model_name: 'prophet_fresh',
    model_version: '1.0.0',
    time_period_days: 30,
    points: [makePerformancePointResponse()],
    ...overrides,
  }
}

/** A mapped comparison, one forecast a day, for component specs. */
export function makePredictionAccuracyPoints(
  overrides: Partial<PredictionAccuracyPoints> = {},
  count = 5,
): PredictionAccuracyPoints {
  const dayMs = 24 * 60 * 60 * 1000
  const startMs = Date.UTC(2026, 8, 10, 6)

  return {
    source: 'simulated',
    horizon: '24h',
    modelName: 'prophet_fresh',
    modelVersion: '1.0.0',
    periodDays: 30,
    points: Array.from({ length: count }, (_, index) => {
      const timeMs = startMs + index * dayMs
      const actual = 64_000 + index * 250
      return {
        time: new Date(timeMs).toISOString(),
        timeMs,
        predicted: actual * 1.01,
        actual,
        marketCondition: 'bull' as const,
      }
    }),
    ...overrides,
  }
}
