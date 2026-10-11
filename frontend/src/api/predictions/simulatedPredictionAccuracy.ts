import type {
  MarketBreakdownEntryResponse,
  MarketCondition,
  ModelHistoryPointResponse,
  PerformanceEntryResponse,
  PerformancePointResponse,
  PerformancePointsResponse,
  PerformanceResponse,
  PredictionAccuracyParams,
  PredictionAccuracyPointsParams,
  ThresholdStatusResponse,
} from '@/types/predictionAccuracy'
import type { PredictionHorizon } from '@/types/predictions'

const DAY_MS = 24 * 60 * 60 * 1000

/** Mean BTC price the simulated USD errors are scaled against. */
const MEAN_PRICE = 82_000

/** `threshold_*` defaults in the ai-service config, all in percent. */
const MAE_PCT_THRESHOLD = 10
const RMSE_PCT_THRESHOLD = 15
const MAPE_THRESHOLD = 10
const WARNING_STREAK_DAYS = 3

/** Days a simulated breach has lasted — one past the streak, so it warns. */
const SIMULATED_BREACH_DAYS = WARNING_STREAK_DAYS + 1

/** Daily aggregation lands at 06:00 UTC, like the service's scheduled job. */
const AGGREGATION_HOUR_UTC = 6

/** The `fresh` strategies the service trains on every cadence. */
const MODELS = ['prophet_fresh', 'xgboost_fresh', 'lightgbm_fresh'] as const

type ModelName = (typeof MODELS)[number]

/** The model the simulated response names as `best_model`. */
const BEST_MODEL: ModelName = 'prophet_fresh'

/**
 * Headline figures per horizon. The 7d model's miss sits just over the MAPE
 * ceiling so the warning path is visible without a backend. `directional` only
 * feeds the history series: like the service today, the summary metrics and
 * threshold checks carry no directional figure.
 */
const BASE: Record<
  PredictionHorizon,
  { mape: number; directional: number; samplesPerDay: number }
> = {
  '24h': { mape: 1.8, directional: 61.5, samplesPerDay: 24 },
  '7d': { mape: 10.8, directional: 53.2, samplesPerDay: 1 },
}

const MODEL_OFFSET: Record<ModelName, { mape: number; directional: number }> =
  {
    prophet_fresh: { mape: 0, directional: 0 },
    xgboost_fresh: { mape: 0.4, directional: -1.5 },
    lightgbm_fresh: { mape: 0.25, directional: -0.8 },
  }

/** Share of samples in each market condition, and how much harder it is. */
const MARKET_MIX: Record<
  MarketCondition,
  { share: number; mapeScale: number }
> = {
  bull: { share: 0.35, mapeScale: 0.85 },
  bear: { share: 0.25, mapeScale: 1.1 },
  volatile: { share: 0.15, mapeScale: 1.6 },
  neutral: { share: 0.25, mapeScale: 0.75 },
}

/**
 * Market each simulated day falls in, spread to match `MARKET_MIX` shares
 * (7 bull, 5 bear, 3 volatile, 5 neutral in every 20 days).
 */
const MARKET_DAYS: MarketCondition[] = [
  'bull', 'bear', 'neutral', 'bull', 'volatile',
  'bear', 'bull', 'neutral', 'bull', 'bear',
  'volatile', 'neutral', 'bull', 'bear', 'neutral',
  'bull', 'volatile', 'bear', 'neutral', 'bull',
]

function isSimulatedModel(modelName: string): modelName is ModelName {
  return (MODELS as readonly string[]).includes(modelName)
}

/** A model's average % miss on a horizon; unknown models get the baseline. */
function modelMape(modelName: string, horizon: PredictionHorizon) {
  const offset = isSimulatedModel(modelName) ? MODEL_OFFSET[modelName].mape : 0
  return BASE[horizon].mape + offset
}

function round(value: number, digits = 2) {
  const factor = 10 ** digits
  return Math.round(value * factor) / factor
}

/** Deterministic wobble, so the same moment always yields the same series. */
function wobble(index: number, amplitude: number) {
  return Math.sin(index * 0.9) * amplitude + Math.cos(index * 0.37) * amplitude
}

function lastAggregationAt(nowMs: number) {
  const at = new Date(nowMs)
  at.setUTCHours(AGGREGATION_HOUR_UTC, 0, 0, 0)

  if (at.getTime() > nowMs) {
    at.setUTCDate(at.getUTCDate() - 1)
  }

  return at.getTime()
}

function usdFromPct(pct: number) {
  return round((pct / 100) * MEAN_PRICE)
}

function buildHistory(
  mape: number,
  directional: number,
  samplesPerDay: number,
  days: number,
  endMs: number,
): ModelHistoryPointResponse[] {
  return Array.from({ length: days }, (_, index) => {
    const pointMape = Math.max(0.2, mape + wobble(index, mape * 0.12))
    const pointDirectional = directional + wobble(index + 3, 2.2)

    return {
      calculated_at: new Date(endMs - (days - 1 - index) * DAY_MS).toISOString(),
      mae: usdFromPct(pointMape),
      rmse: usdFromPct(pointMape * 1.35),
      mape: round(pointMape),
      directional_accuracy: round(pointDirectional, 1),
      sample_size: samplesPerDay,
    }
  })
}

function thresholdStatus(
  metric: ThresholdStatusResponse['metric'],
  value: number,
  threshold: number,
  direction: 'above' | 'below',
): ThresholdStatusResponse {
  const breached = direction === 'above' ? value > threshold : value < threshold

  return {
    metric,
    value: round(value),
    threshold,
    breached,
    breach_direction: direction,
    consecutive_days: breached ? SIMULATED_BREACH_DAYS : 0,
    warning: breached,
  }
}

function buildEntry(
  model: ModelName,
  horizon: PredictionHorizon,
  days: number,
  endMs: number,
): PerformanceEntryResponse {
  const base = BASE[horizon]
  const offset = MODEL_OFFSET[model]
  const mape = modelMape(model, horizon)
  const directional = base.directional + offset.directional
  const samples = base.samplesPerDay * days
  const history = buildHistory(
    mape,
    directional,
    base.samplesPerDay,
    days,
    endMs,
  )

  // MAE and MAPE share a scale here (both % of the same mean price), so they
  // breach together — as they would on the service.
  const thresholds = [
    thresholdStatus('mae_pct', mape, MAE_PCT_THRESHOLD, 'above'),
    thresholdStatus('rmse_pct', mape * 1.35, RMSE_PCT_THRESHOLD, 'above'),
    thresholdStatus('mape', mape, MAPE_THRESHOLD, 'above'),
  ]
  const warnings = thresholds.filter((threshold) => threshold.warning)

  const market_breakdown = Object.fromEntries(
    Object.entries(MARKET_MIX).map(([condition, mix]) => {
      const bucketMape = mape * mix.mapeScale
      const bucket: MarketBreakdownEntryResponse = {
        mae: usdFromPct(bucketMape),
        rmse: usdFromPct(bucketMape * 1.35),
        mape: round(bucketMape),
        samples: Math.round(samples * mix.share),
      }
      return [condition, bucket]
    }),
  )

  return {
    model_name: model,
    model_version: '1.0.0',
    horizon,
    samples,
    metrics: {
      mae: usdFromPct(mape),
      rmse: usdFromPct(mape * 1.35),
      mape: round(mape),
      // The service does not compute this per entry yet (`performance.py`).
      directional_accuracy: null,
    },
    market_breakdown,
    thresholds,
    recent_breach_count: warnings.length * SIMULATED_BREACH_DAYS,
    last_updated: new Date(endMs).toISOString(),
    warning: warnings.length > 0,
    warning_count: warnings.length,
    warning_threshold_days: WARNING_STREAK_DAYS,
    history,
  }
}

/**
 * Stand-in `GET /api/v1/performance/btc` body for a frontend-only run.
 *
 * Shaped exactly like the service's `PerformanceResponse` with
 * `include_history=true`, and filled the way the service fills it today, so
 * what the card shows here is what it will show live.
 */
export function buildSimulatedPerformance(
  params: PredictionAccuracyParams,
  nowMs: number,
): PerformanceResponse {
  const endMs = lastAggregationAt(nowMs)
  const entries = MODELS.map((model) =>
    buildEntry(model, params.horizon, params.days, endMs),
  )

  return {
    time_period_days: params.days,
    generated_at: new Date(nowMs).toISOString(),
    entries,
    warnings_count: entries.reduce(
      (total, entry) => total + entry.warning_count,
      0,
    ),
    best_model: BEST_MODEL,
  }
}

/**
 * A BTC price path both horizons are scored against, keyed on time so a 24h
 * and a 7d forecast for the same moment meet the same actual price.
 */
function simulatedActualPrice(timeMs: number) {
  const days = timeMs / DAY_MS
  return (
    MEAN_PRICE *
    (1 +
      Math.sin(days * 0.35) * 0.04 +
      Math.cos(days * 0.9) * 0.025 +
      Math.sin(days * 24 * 1.7) * 0.0015)
  )
}

/**
 * Stand-in `GET /api/v1/performance/btc/points` body for a frontend-only run.
 *
 * One point per scored forecast, as many as the accuracy entry counts, each
 * missing by about that model's average % miss — scaled by how hard its
 * market is — so the gap on the chart matches the MAPE on the card.
 */
export function buildSimulatedPerformancePoints(
  params: PredictionAccuracyPointsParams,
  nowMs: number,
): PerformancePointsResponse {
  const modelName = params.modelName ?? BEST_MODEL
  const { samplesPerDay } = BASE[params.horizon]
  const mape = modelMape(modelName, params.horizon)
  const endMs = lastAggregationAt(nowMs)
  const stepMs = DAY_MS / samplesPerDay
  const count = samplesPerDay * params.days

  const times = Array.from(
    { length: count },
    (_, index) => endMs - (count - 1 - index) * stepMs,
  )
  const conditions = times.map(
    (timeMs) => MARKET_DAYS[Math.floor(timeMs / DAY_MS) % MARKET_DAYS.length],
  )
  // A real model's error drifts: it runs over or under for days at a time,
  // not in a regular back-and-forth. Two slow, unrelated waves give that
  // irregular drift, weighted by how hard each market is. Dividing by the
  // mean size brings the average miss back to the MAPE the card reports.
  const drift = times.map((timeMs, index) => {
    const day = timeMs / DAY_MS
    const wave = 0.65 * Math.sin(day * 0.21) + 0.35 * Math.sin(day * 0.57 + 1.3)
    return wave * MARKET_MIX[conditions[index]].mapeScale
  })
  const meanDrift =
    drift.reduce((total, value) => total + Math.abs(value), 0) /
      drift.length || 1

  const points = times.map((timeMs, index) => {
    const condition = conditions[index]
    const actual = simulatedActualPrice(timeMs)
    const missPct = (mape * drift[index]) / meanDrift
    const point: PerformancePointResponse = {
      forecast_date: new Date(timeMs).toISOString(),
      predicted_price: round(actual * (1 + missPct / 100)),
      actual_price: round(actual),
      market_condition: condition,
    }
    return point
  })

  return {
    horizon: params.horizon,
    model_name: modelName,
    model_version: '1.0.0',
    time_period_days: params.days,
    points,
  }
}
