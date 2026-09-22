import type {
  BtcPrediction,
  PredictionHistory,
  PredictionPoint,
} from '@/types/predictions'

export function makePredictionPoint(
  overrides: Partial<PredictionPoint> = {},
): PredictionPoint {
  const timeMs = overrides.timeMs ?? Date.UTC(2024, 5, 15, 13)

  return {
    time: new Date(timeMs).toISOString(),
    timeMs,
    predictedPrice: 64_000,
    lowerBound: 63_500,
    upperBound: 64_500,
    ...overrides,
  }
}

/** A mapped batch in the shape the fetcher returns, for component specs. */
export function makePrediction(
  overrides: Partial<BtcPrediction> = {},
): BtcPrediction {
  return {
    source: 'simulated',
    horizon: '24h',
    modelName: 'prophet',
    confidence: 0.85,
    predictionTime: '2024-06-15T12:00:00.000Z',
    currentPrice: 63_500,
    predictedEndPrice: 64_200,
    priceChangePct: 1.1,
    trend: 'up',
    points: [
      makePredictionPoint({
        timeMs: Date.UTC(2024, 5, 15, 13),
        lowerBound: 63_800,
        upperBound: 64_200,
      }),
      makePredictionPoint({
        timeMs: Date.UTC(2024, 5, 15, 14),
        lowerBound: 63_400,
        upperBound: 64_900,
      }),
    ],
    ...overrides,
  }
}

/** Candles behind a forecast, in the shape the history fetcher returns. */
export function makePredictionHistory(
  overrides: Partial<PredictionHistory> = {},
): PredictionHistory {
  const startMs = Date.UTC(2024, 5, 15, 10)

  return {
    source: 'simulated',
    range: '24h',
    interval: '1h',
    candles: Array.from({ length: 3 }, (_, index) => {
      const timeMs = startMs + index * 60 * 60 * 1000
      return {
        time: new Date(timeMs).toISOString(),
        timeMs,
        open: 63_000 + index * 100,
        high: 63_400 + index * 100,
        low: 62_900 + index * 100,
        close: 63_200 + index * 100,
      }
    }),
    ...overrides,
  }
}
