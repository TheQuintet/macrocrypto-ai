import type { ChartCandle } from '@/types/chart'

/**
 * BTC price predictions — GET /api/v1/predict/btc on the ai-service.
 *
 * Wire shapes mirror `PredictionResponse` in
 * `services/ai-service/app/schemas/prediction.py`; UI shapes are the
 * camel-cased projection the components consume.
 */

/** Forecast window the endpoint supports. */
export type PredictionHorizon = '24h' | '7d'

/** Confidence levels the endpoint produces bounds for. */
export type PredictionConfidence = 0.7 | 0.85 | 0.95

/** `TrendDirection` on the wire. */
export type PredictionTrend = 'up' | 'down' | 'neutral'

/** Live API vs frontend stand-in — set by the fetcher, never by the UI. */
export type PredictionSource = 'live' | 'simulated'

/** How wide the confidence band is relative to the predicted price. */
export type PredictionBandWidth = 'narrow' | 'medium' | 'wide'

export type PredictionParams = {
  horizon: PredictionHorizon
  confidence: PredictionConfidence
}

/** One forecast row on the wire. */
export type PredictionPointResponse = {
  time: string
  predicted_price: number
  lower_bound: number
  upper_bound: number
}

/** `PredictionResponse` on the wire. */
export type PredictionResponse = {
  horizon: string
  model_name: string
  confidence: number
  prediction_time: string
  current_price: number | null
  predicted_end_price: number
  price_change_pct: number | null
  trend: PredictionTrend
  predictions: PredictionPointResponse[]
}

export type PredictionPoint = {
  time: string
  timeMs: number
  predictedPrice: number
  lowerBound: number
  upperBound: number
}

/** A single-model forecast batch, as the Forecasts screen consumes it. */
export type BtcPrediction = {
  source: PredictionSource
  horizon: PredictionHorizon
  modelName: string
  confidence: number
  predictionTime: string
  currentPrice: number | null
  predictedEndPrice: number
  priceChangePct: number | null
  trend: PredictionTrend
  points: PredictionPoint[]
}

/** Widest bounds across the batch — the window's expected price levels. */
export type PredictionKeyLevels = {
  high: number
  low: number
}

/** Candle size the history behind each horizon is fetched at. */
export type PredictionHistoryInterval = '1h' | '1d'

/**
 * Lookback windows the data service serves. Wider than the forecast horizons
 * on purpose: a week-ahead forecast reads better against a month of price.
 */
export type PredictionHistoryRange = '24h' | '7d' | '30d'

/**
 * `BtcPriceHistoryResponse` as the data service actually serves it.
 *
 * Declared here rather than reusing `@/types/btcPriceHistory`: that type pins
 * `range` to the dashboard picker's `TimeRange` (30d/90d/1y/5y), while the
 * endpoint itself also accepts the 24h and 7d windows a forecast needs.
 */
export type PredictionHistoryResponse = {
  range: string
  interval: string
  points: {
    timestamp: string
    open: number
    high: number
    low: number
    close: number
  }[]
}

/** GET /api/v1/btc/price/history, scoped to a forecast horizon. */
export type PredictionHistoryParams = {
  /** The forecast this history sits behind — not sent, but it sizes the window. */
  horizon: PredictionHorizon
  range: PredictionHistoryRange
  interval: PredictionHistoryInterval
}

/** Actual price behind the forecast, as the chart consumes it. */
export type PredictionHistory = {
  source: PredictionSource
  range: PredictionHistoryRange
  interval: PredictionHistoryInterval
  candles: ChartCandle[]
}

/** Which half of the plot a row belongs to. */
export type PredictionRowKind = 'history' | 'forecast'

/**
 * One plotted row. A row is a moment in time, carrying whatever is known
 * about it — so the model's line and the actual candles share the same rows
 * over the history rather than sitting beside each other.
 *
 * `fit` is the model's in-sample value for a moment that has already
 * happened; `predicted` is its forecast for one that has not. The row at the
 * boundary carries both, so the two lines join instead of breaking.
 */
export type PredictionChartRow = {
  kind: PredictionRowKind
  time: string
  timeMs: number
  open?: number
  high?: number
  low?: number
  close?: number
  /** The `[low, high]` pair the candle bar spans, where a candle exists. */
  candle?: [number, number]
  /** Model value over history — what it would have said at the time. */
  fit?: number
  /** Model value ahead of now. */
  predicted?: number
  lower?: number
  upper?: number
  /** The `[lower, upper]` pair the band area spans. */
  band?: [number, number]
}
