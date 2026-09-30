import type { PredictionHorizon, PredictionSource } from '@/types/predictions'

/**
 * Historical forecast accuracy — GET /api/v1/performance/btc on the ai-service.
 *
 * Wire shapes mirror `PerformanceResponse` in
 * `services/ai-service/app/schemas/performance.py`; UI shapes are the
 * camel-cased projection of the one entry the Forecasts screen shows.
 */

/** Market-condition buckets the service classifies each window into. */
export type MarketCondition = 'bull' | 'bear' | 'volatile' | 'neutral'

/** `PerformanceMetrics` on the wire. MAE/RMSE in USD, the rest in percent. */
export type PerformanceMetricsResponse = {
  mae: number | null
  rmse: number | null
  mape: number | null
  directional_accuracy: number | null
}

/** `MarketBreakdownEntry` on the wire. */
export type MarketBreakdownEntryResponse = {
  mae: number | null
  rmse: number | null
  mape: number | null
  samples: number
}

/** `ThresholdStatus` on the wire. */
export type ThresholdStatusResponse = {
  metric: string
  value: number
  threshold: number
  breached: boolean
  breach_direction: string
  consecutive_days: number
  warning: boolean
}

/** `ModelHistoryPoint` on the wire. */
export type ModelHistoryPointResponse = {
  calculated_at: string
  mae: number | null
  rmse: number | null
  mape: number | null
  directional_accuracy: number | null
  sample_size: number
}

/** `PerformanceEntry` on the wire — one (model, horizon) pair. */
export type PerformanceEntryResponse = {
  model_name: string
  model_version: string | null
  horizon: string
  samples: number
  metrics: PerformanceMetricsResponse
  market_breakdown: Record<string, MarketBreakdownEntryResponse>
  thresholds: ThresholdStatusResponse[]
  recent_breach_count: number
  last_updated: string | null
  warning: boolean
  warning_count: number
  warning_threshold_days: number
  history: ModelHistoryPointResponse[]
}

/** `PerformanceResponse` on the wire. */
export type PerformanceResponse = {
  time_period_days: number
  generated_at: string
  entries: PerformanceEntryResponse[]
  warnings_count: number
  best_model: string | null
}

export type PredictionAccuracyParams = {
  horizon: PredictionHorizon
  days: number
}

export type AccuracyMetrics = {
  /** Mean absolute error, USD. */
  mae: number | null
  /** Root mean square error, USD. */
  rmse: number | null
  /** Mean absolute percentage error, percent. */
  mape: number | null
  /** Share of calls with the right direction, percent. */
  directionalAccuracy: number | null
}

export type MarketBreakdownRow = {
  condition: MarketCondition
  mae: number | null
  mape: number | null
  samples: number
}

export type AccuracyThreshold = {
  metric: string
  value: number
  threshold: number
  breached: boolean
  /** `above` for error metrics, `below` for directional accuracy. */
  breachDirection: 'above' | 'below'
  consecutiveDays: number
  warning: boolean
}

export type AccuracyHistoryPoint = {
  time: string
  timeMs: number
  mape: number | null
  directionalAccuracy: number | null
  sampleSize: number
}

/** The model entry the Forecasts screen reports accuracy for. */
export type PredictionAccuracy = {
  source: PredictionSource
  horizon: PredictionHorizon
  modelName: string
  modelVersion: string | null
  /** True when this entry is the service's overall `best_model`. */
  isBestModel: boolean
  periodDays: number
  samples: number
  lastUpdated: string | null
  metrics: AccuracyMetrics
  marketBreakdown: MarketBreakdownRow[]
  thresholds: AccuracyThreshold[]
  /** Service-wide flag; can be set for a metric missing from `thresholds`. */
  warning: boolean
  warningCount: number
  warningThresholdDays: number
  history: AccuracyHistoryPoint[]
}

/** Which figure the headline score was taken from. */
export type AccuracyScoreKind = 'directional' | 'price'

export type AccuracyScore = {
  kind: AccuracyScoreKind
  /** 0–100. */
  value: number
}
