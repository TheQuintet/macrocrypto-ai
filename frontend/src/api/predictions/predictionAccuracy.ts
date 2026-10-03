import { BTC_PREDICTION_PERFORMANCE_PATH } from '@/constants/apiUrls'
import { apiUrl } from '@/lib/apiConfig'
import { buildSimulatedPerformance } from '@/api/predictions/simulatedPredictionAccuracy'
import type {
  AccuracyThreshold,
  MarketBreakdownRow,
  MarketCondition,
  ModelHistoryPointResponse,
  PerformanceEntryResponse,
  PerformanceResponse,
  PredictionAccuracy,
  PredictionAccuracyParams,
  ThresholdStatusResponse,
} from '@/types/predictionAccuracy'
import type { PredictionHorizon, PredictionSource } from '@/types/predictions'

/** The service re-aggregates once a day; a few minutes stale is plenty fresh. */
export const PREDICTION_ACCURACY_STALE_MS = 15 * 60 * 1000

/**
 * Look-back window the card reports on ("based on the last 90 days").
 *
 * 90, not 30, so the trend covers about three months: the service fetches
 * history inside `days` and only then trims it to `history_limit` (capped at
 * 90), so a longer trend needs a longer window for every figure.
 */
export const PREDICTION_ACCURACY_DAYS = 90

/** `MAX_HISTORY_LIMIT` on the service; asking for more is a 422. */
const HISTORY_LIMIT_MAX = 90

const MOCK_LATENCY_MS = 200

/** Display order for the market-condition breakdown. */
const MARKET_CONDITIONS: MarketCondition[] = [
  'bull',
  'bear',
  'volatile',
  'neutral',
]

export function predictionAccuracyQueryKey(params: PredictionAccuracyParams) {
  return ['btc-prediction-accuracy', params.horizon, params.days] as const
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/** One horizon, with the history series the trend chart draws. */
export function predictionAccuracySearchParams(
  params: PredictionAccuracyParams,
) {
  return new URLSearchParams({
    horizon: params.horizon,
    days: String(params.days),
    include_history: 'true',
    // One point per day, up to the service's cap — `days` itself goes to 365.
    history_limit: String(Math.min(params.days, HISTORY_LIMIT_MAX)),
  })
}

/**
 * The entry to report for a horizon: the service's `best_model` when it has
 * one there, otherwise the lowest-MAPE model, otherwise whatever came first.
 */
export function pickAccuracyEntry(
  response: PerformanceResponse,
  horizon: PredictionHorizon,
): PerformanceEntryResponse | null {
  const entries = response.entries.filter((entry) => entry.horizon === horizon)

  if (entries.length === 0) {
    return null
  }

  const best = entries.find((entry) => entry.model_name === response.best_model)
  if (best) {
    return best
  }

  const scored = entries.filter((entry) => entry.metrics.mape != null)
  if (scored.length > 0) {
    return scored.reduce((lowest, entry) =>
      entry.metrics.mape! < lowest.metrics.mape! ? entry : lowest,
    )
  }

  return entries[0]
}

function mapMarketBreakdown(
  breakdown: PerformanceEntryResponse['market_breakdown'],
): MarketBreakdownRow[] {
  return MARKET_CONDITIONS.flatMap((condition) => {
    const bucket = breakdown[condition]
    return bucket
      ? [
          {
            condition,
            mae: bucket.mae,
            mape: bucket.mape,
            samples: bucket.samples,
          },
        ]
      : []
  })
}

function mapThreshold(threshold: ThresholdStatusResponse): AccuracyThreshold {
  return {
    metric: threshold.metric,
    value: threshold.value,
    threshold: threshold.threshold,
    breached: threshold.breached,
    breachDirection:
      threshold.breach_direction === 'below' ? 'below' : 'above',
    consecutiveDays: threshold.consecutive_days,
    warning: threshold.warning,
  }
}

function mapHistoryPoint(point: ModelHistoryPointResponse) {
  return {
    time: point.calculated_at,
    timeMs: new Date(point.calculated_at).getTime(),
    mape: point.mape,
    directionalAccuracy: point.directional_accuracy,
    sampleSize: point.sample_size,
  }
}

/**
 * Wire -> UI mapping; the only piece the live endpoint landing has to keep.
 * Null when the service has no entry for the horizon yet.
 */
export function mapPredictionAccuracy(
  response: PerformanceResponse,
  horizon: PredictionHorizon,
  source: PredictionSource = 'live',
): PredictionAccuracy | null {
  const entry = pickAccuracyEntry(response, horizon)

  if (!entry) {
    return null
  }

  return {
    source,
    horizon,
    modelName: entry.model_name,
    modelVersion: entry.model_version,
    isBestModel: entry.model_name === response.best_model,
    periodDays: response.time_period_days,
    samples: entry.samples,
    lastUpdated: entry.last_updated,
    metrics: {
      mae: entry.metrics.mae,
      rmse: entry.metrics.rmse,
      mape: entry.metrics.mape,
      directionalAccuracy: entry.metrics.directional_accuracy,
    },
    marketBreakdown: mapMarketBreakdown(entry.market_breakdown),
    thresholds: entry.thresholds.map(mapThreshold),
    warning: entry.warning,
    warningCount: entry.warning_count,
    warningThresholdDays: entry.warning_threshold_days,
    history: entry.history.map(mapHistoryPoint),
  }
}

/** Stand-in accuracy for a frontend-only run, labelled as simulated. */
export async function simulatePredictionAccuracy(
  params: PredictionAccuracyParams,
  nowMs = Date.now(),
): Promise<PredictionAccuracy | null> {
  await delay(MOCK_LATENCY_MS)

  return mapPredictionAccuracy(
    buildSimulatedPerformance(params, nowMs),
    params.horizon,
    'simulated',
  )
}

/**
 * Historical forecast accuracy from the ai-service.
 *
 * With no backend configured the card runs on simulated data so it still
 * works standalone. When a backend *is* configured a failed request throws
 * rather than substituting invented scores — a made-up "87% accurate" is
 * exactly the number a trader must not be shown.
 *
 * Note: the API gateway does not yet proxy the ai-service, so a full-stack
 * run currently 404s here and surfaces that error state. Routing it is a
 * backend task; nothing on this path changes when it lands.
 */
export async function fetchPredictionAccuracy(
  params: PredictionAccuracyParams,
  nowMs = Date.now(),
): Promise<PredictionAccuracy | null> {
  const url = apiUrl(BTC_PREDICTION_PERFORMANCE_PATH)

  if (!url) {
    return simulatePredictionAccuracy(params, nowMs)
  }

  const response = await fetch(
    `${url}?${predictionAccuracySearchParams(params)}`,
    { headers: { Accept: 'application/json' } },
  )

  if (!response.ok) {
    throw new Error(`Accuracy request failed with ${response.status}`)
  }

  return mapPredictionAccuracy(
    (await response.json()) as PerformanceResponse,
    params.horizon,
    'live',
  )
}
