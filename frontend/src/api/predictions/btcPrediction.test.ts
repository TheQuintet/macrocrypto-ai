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
  HISTORY_WINDOW,
  PREDICTION_POINT_COUNT,
} from '@/api/predictions/predictionWindow'
import type { PredictionResponse } from '@/types/predictions'

const FIXED_NOW_MS = Date.UTC(2024, 5, 15, 12, 0, 0)

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
  it('fits back across every candle it will be drawn over', () => {
    const response = buildSimulatedPrediction(
      { horizon: '7d', confidence: 0.85 },
      FIXED_NOW_MS,
    )
    const boundaryMs = new Date(response.prediction_time).getTime()
    const behind = response.predictions.filter(
      (point) => new Date(point.time).getTime() <= boundaryMs,
    )

    expect(behind).toHaveLength(HISTORY_WINDOW['7d'].candles)
  })

  it('covers the window behind now as well as the one ahead', () => {
    const response = buildSimulatedPrediction(
      { horizon: '24h', confidence: 0.85 },
      FIXED_NOW_MS,
    )
    const boundaryMs = new Date(response.prediction_time).getTime()
    const ahead = response.predictions.filter(
      (point) => new Date(point.time).getTime() > boundaryMs,
    )
    const behind = response.predictions.filter(
      (point) => new Date(point.time).getTime() <= boundaryMs,
    )

    expect(ahead).toHaveLength(PREDICTION_POINT_COUNT['24h'])
    expect(behind).toHaveLength(HISTORY_WINDOW['24h'].candles)
  })

  it('returns one forecast point per hour for 24h and per day for 7d', () => {
    const forecastCount = (horizon: '24h' | '7d') => {
      const response = buildSimulatedPrediction(
        { horizon, confidence: 0.85 },
        FIXED_NOW_MS,
      )
      const boundaryMs = new Date(response.prediction_time).getTime()
      return response.predictions.filter(
        (point) => new Date(point.time).getTime() > boundaryMs,
      ).length
    }

    expect(forecastCount('24h')).toBe(PREDICTION_POINT_COUNT['24h'])
    expect(forecastCount('7d')).toBe(PREDICTION_POINT_COUNT['7d'])
  })

  it('keeps the in-sample band tighter than the forecast cone', () => {
    const response = buildSimulatedPrediction(
      { horizon: '24h', confidence: 0.85 },
      FIXED_NOW_MS,
    )
    const boundaryMs = new Date(response.prediction_time).getTime()
    const width = (point: (typeof response.predictions)[number]) =>
      point.upper_bound - point.lower_bound
    const behind = response.predictions.filter(
      (point) => new Date(point.time).getTime() <= boundaryMs,
    )
    const ahead = response.predictions.filter(
      (point) => new Date(point.time).getTime() > boundaryMs,
    )

    expect(width(behind[0])).toBeLessThan(width(ahead[ahead.length - 1]))
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
    expect(prediction.points).toHaveLength(
      PREDICTION_POINT_COUNT['24h'] + HISTORY_WINDOW['24h'].candles,
    )
  })
})
