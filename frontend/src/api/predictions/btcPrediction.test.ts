import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  btcPredictionQueryKey,
  btcPredictionSearchParams,
  mapBtcPrediction,
  simulateBtcPrediction,
} from '@/api/predictions/btcPrediction'
import {
  buildSimulatedPrediction,
  simulatedCurrentPrice,
} from '@/api/predictions/simulatedBtcPrediction'
import {
  PREDICTION_POINT_COUNT,
  PREDICTION_STEP_MS,
} from '@/api/predictions/predictionWindow'
import type { PredictionResponse } from '@/types/predictions'

const FIXED_NOW_MS = Date.UTC(2024, 5, 15, 12, 0, 0)
const HOUR_MS = 60 * 60 * 1000

/** A real `GET /api/v1/predict/btc` body, as `PredictionResponse` serialises it. */
const WIRE_RESPONSE: PredictionResponse = {
  horizon: '24h',
  model_name: 'prophet',
  confidence: 0.85,
  prediction_time: '2024-06-15T12:00:00.000Z',
  current_price: 63_500.42,
  predicted_end_price: 64_200.75,
  price_change_pct: 1.1,
  trend: 'up',
  predictions: [
    {
      time: '2024-06-15T13:00:00.000Z',
      predicted_price: 63_550.1,
      lower_bound: 63_400,
      upper_bound: 63_700.2,
    },
  ],
}

describe('btcPredictionQueryKey', () => {
  it('keys by horizon and confidence so each batch caches separately', () => {
    expect(btcPredictionQueryKey({ horizon: '24h', confidence: 0.85 })).toEqual(
      ['btc-prediction', '24h', 0.85],
    )
    expect(
      btcPredictionQueryKey({ horizon: '7d', confidence: 0.95 }),
    ).not.toEqual(btcPredictionQueryKey({ horizon: '7d', confidence: 0.7 }))
  })
})

describe('btcPredictionSearchParams', () => {
  it('sends horizon and confidence', () => {
    const params = btcPredictionSearchParams({
      horizon: '7d',
      confidence: 0.95,
    })

    expect(params.get('horizon')).toBe('7d')
    expect(params.get('confidence')).toBe('0.95')
  })

  it('omits `models`, which would switch the endpoint to a comparison shape', () => {
    const params = btcPredictionSearchParams({
      horizon: '24h',
      confidence: 0.85,
    })

    expect(params.has('models')).toBe(false)
  })
})

describe('mapBtcPrediction', () => {
  it('camel-cases the service payload', () => {
    expect(mapBtcPrediction(WIRE_RESPONSE)).toEqual({
      source: 'live',
      horizon: '24h',
      modelName: 'prophet',
      confidence: 0.85,
      predictionTime: '2024-06-15T12:00:00.000Z',
      currentPrice: 63_500.42,
      predictedEndPrice: 64_200.75,
      priceChangePct: 1.1,
      trend: 'up',
      points: [
        {
          time: '2024-06-15T13:00:00.000Z',
          timeMs: Date.UTC(2024, 5, 15, 13),
          predictedPrice: 63_550.1,
          lowerBound: 63_400,
          upperBound: 63_700.2,
        },
      ],
    })
  })

  it('preserves the nulls the service sends with no current price', () => {
    const prediction = mapBtcPrediction({
      ...WIRE_RESPONSE,
      current_price: null,
      price_change_pct: null,
    })

    expect(prediction.currentPrice).toBeNull()
    expect(prediction.priceChangePct).toBeNull()
  })
})

describe('buildSimulatedPrediction', () => {
  /**
   * The ai-service builds its frame from the last training row plus an hour
   * and never returns in-sample fitted values, so neither does the stand-in.
   */
  it('returns forward points only, like the endpoint', () => {
    for (const horizon of ['24h', '7d'] as const) {
      const response = buildSimulatedPrediction(
        { horizon, confidence: 0.85 },
        FIXED_NOW_MS,
      )
      const boundaryMs = new Date(response.prediction_time).getTime()

      expect(
        response.predictions.every(
          (point) => new Date(point.time).getTime() > boundaryMs,
        ),
      ).toBe(true)
    }
  })

  it('returns hourly points for both horizons: 24 for 24h, 168 for 7d', () => {
    for (const horizon of ['24h', '7d'] as const) {
      const { predictions } = buildSimulatedPrediction(
        { horizon, confidence: 0.85 },
        FIXED_NOW_MS,
      )
      const times = predictions.map((point) => new Date(point.time).getTime())

      expect(predictions).toHaveLength(PREDICTION_POINT_COUNT[horizon])
      expect(
        times.slice(1).every((time, index) => time - times[index] === HOUR_MS),
      ).toBe(true)
    }

    expect(PREDICTION_POINT_COUNT['7d']).toBe(168)
    expect(PREDICTION_STEP_MS['7d']).toBe(HOUR_MS)
  })

  it('is deterministic for a moment in time', () => {
    const params = { horizon: '24h', confidence: 0.85 } as const

    expect(buildSimulatedPrediction(params, FIXED_NOW_MS)).toEqual(
      buildSimulatedPrediction(params, FIXED_NOW_MS),
    )
  })

  it('keeps every bound straddling its predicted price', () => {
    const { predictions } = buildSimulatedPrediction(
      { horizon: '7d', confidence: 0.7 },
      FIXED_NOW_MS,
    )

    for (const point of predictions) {
      expect(point.lower_bound).toBeLessThan(point.predicted_price)
      expect(point.upper_bound).toBeGreaterThan(point.predicted_price)
    }
  })

  it('widens the band as the confidence level rises', () => {
    const widthAt = (confidence: 0.7 | 0.85 | 0.95) => {
      const [first] = buildSimulatedPrediction(
        { horizon: '24h', confidence },
        FIXED_NOW_MS,
      ).predictions
      return first.upper_bound - first.lower_bound
    }

    expect(widthAt(0.85)).toBeGreaterThan(widthAt(0.7))
    expect(widthAt(0.95)).toBeGreaterThan(widthAt(0.85))
  })

  it('fans the band out further along the horizon', () => {
    const { predictions } = buildSimulatedPrediction(
      { horizon: '7d', confidence: 0.85 },
      FIXED_NOW_MS,
    )
    const width = (index: number) =>
      predictions[index].upper_bound - predictions[index].lower_bound

    expect(width(predictions.length - 1)).toBeGreaterThan(width(0))
  })

  it('derives the change and trend from the anchor price', () => {
    const response = buildSimulatedPrediction(
      { horizon: '24h', confidence: 0.85 },
      FIXED_NOW_MS,
    )
    const last = response.predictions[response.predictions.length - 1]

    expect(response.current_price).toBe(simulatedCurrentPrice(FIXED_NOW_MS))
    expect(response.predicted_end_price).toBe(last.predicted_price)
  })

  /**
   * The projection follows the same curve the candles came from, so its
   * direction is whatever that window was doing — not a fixed climb.
   */
  /** Plus or minus 0.5% for 24h and 1.0% for 7d, exclusive, as the ai-service. */
  it('applies the ai-service trend threshold for each horizon', () => {
    const thresholds = { '24h': 0.5, '7d': 1 } as const
    let withinWeeklyBand = 0

    for (const horizon of ['24h', '7d'] as const) {
      for (let offset = 0; offset < 200; offset += 1) {
        const response = buildSimulatedPrediction(
          { horizon, confidence: 0.85 },
          FIXED_NOW_MS + offset * HOUR_MS,
        )
        const changePct = response.price_change_pct!
        const threshold = thresholds[horizon]
        const expected =
          changePct > threshold
            ? 'up'
            : changePct < -threshold
              ? 'down'
              : 'neutral'

        expect(response.trend).toBe(expected)
        if (
          horizon === '7d' &&
          Math.abs(changePct) > 0.5 &&
          Math.abs(changePct) <= 1
        ) {
          withinWeeklyBand += 1
        }
      }
    }

    // Moves a day would call a trend but a week would not: the case that
    // tells the two thresholds apart.
    expect(withinWeeklyBand).toBeGreaterThan(0)
  })

  it('reports a trend that agrees with its own change figure', () => {
    const hour = 60 * 60 * 1000

    for (let offset = 0; offset < 48; offset += 3) {
      const response = buildSimulatedPrediction(
        { horizon: '24h', confidence: 0.85 },
        FIXED_NOW_MS + offset * hour,
      )
      const changePct = response.price_change_pct!

      if (response.trend === 'up') {
        expect(changePct).toBeGreaterThan(0)
      } else if (response.trend === 'down') {
        expect(changePct).toBeLessThan(0)
      }
    }
  })

  it('forecasts downward windows as well as upward ones', () => {
    const hour = 60 * 60 * 1000
    const trends = new Set(
      Array.from({ length: 48 }, (_, index) =>
        buildSimulatedPrediction(
          { horizon: '24h', confidence: 0.85 },
          FIXED_NOW_MS + index * hour,
        ).trend,
      ),
    )

    expect(trends).toContain('up')
    expect(trends).toContain('down')
  })

  it('echoes back the horizon and confidence that were asked for', () => {
    const response = buildSimulatedPrediction(
      { horizon: '7d', confidence: 0.95 },
      FIXED_NOW_MS,
    )

    expect(response.horizon).toBe('7d')
    expect(response.confidence).toBe(0.95)
  })
})

describe('simulateBtcPrediction', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('resolves a mapped batch labelled as simulated', async () => {
    const pending = simulateBtcPrediction(
      { horizon: '24h', confidence: 0.85 },
      FIXED_NOW_MS,
    )
    await vi.advanceTimersByTimeAsync(220)
    const prediction = await pending

    expect(prediction.source).toBe('simulated')
    expect(prediction.horizon).toBe('24h')
    expect(prediction.points).toHaveLength(PREDICTION_POINT_COUNT['24h'])
  })
})
