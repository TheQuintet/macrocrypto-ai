import { BTC_PREDICTION_PERFORMANCE_POINTS_PATH } from '@/constants/apiUrls'
import { apiUrl } from '@/lib/apiConfig'
import { buildSimulatedPerformancePoints } from '@/api/predictions/simulatedPredictionAccuracy'
import type {
  MarketCondition,
  PerformancePointResponse,
  PerformancePointsResponse,
  PredictionAccuracyPoint,
  PredictionAccuracyPoints,
  PredictionAccuracyPointsParams,
} from '@/types/predictionAccuracy'
import type { PredictionHorizon, PredictionSource } from '@/types/predictions'

const MOCK_LATENCY_MS = 200

const MARKET_CONDITIONS: readonly string[] = [
  'bull',
  'bear',
  'volatile',
  'neutral',
] satisfies MarketCondition[]

export function predictionAccuracyPointsQueryKey(
  params: PredictionAccuracyPointsParams,
) {
  return [
    'btc-prediction-accuracy-points',
    params.horizon,
    params.days,
    params.modelName ?? null,
  ] as const
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export function predictionAccuracyPointsSearchParams(
  params: PredictionAccuracyPointsParams,
) {
  const search = new URLSearchParams({
    horizon: params.horizon,
    days: String(params.days),
  })

  if (params.modelName) {
    search.set('model_name', params.modelName)
  }

  return search
}

function mapMarketCondition(condition: string | null): MarketCondition | null {
  return condition != null && MARKET_CONDITIONS.includes(condition)
    ? (condition as MarketCondition)
    : null
}

function mapPoint(point: PerformancePointResponse): PredictionAccuracyPoint {
  return {
    time: point.forecast_date,
    timeMs: new Date(point.forecast_date).getTime(),
    predicted: point.predicted_price,
    actual: point.actual_price,
    marketCondition: mapMarketCondition(point.market_condition),
  }
}

/** Wire -> UI mapping. The service already orders points oldest first. */
export function mapPredictionAccuracyPoints(
  response: PerformancePointsResponse,
  horizon: PredictionHorizon,
  source: PredictionSource = 'live',
): PredictionAccuracyPoints {
  return {
    source,
    horizon,
    modelName: response.model_name,
    modelVersion: response.model_version,
    periodDays: response.time_period_days,
    points: response.points.map(mapPoint),
  }
}

/** Stand-in scored forecasts for a frontend-only run, labelled as simulated. */
export async function simulatePredictionAccuracyPoints(
  params: PredictionAccuracyPointsParams,
  nowMs = Date.now(),
): Promise<PredictionAccuracyPoints> {
  await delay(MOCK_LATENCY_MS)

  return mapPredictionAccuracyPoints(
    buildSimulatedPerformancePoints(params, nowMs),
    params.horizon,
    'simulated',
  )
}

/**
 * Each scored forecast's predicted and actual price, from the ai-service.
 *
 * Same rule as the accuracy figures: simulated only when no backend is
 * configured, and a failed live request throws rather than drawing an
 * invented comparison.
 */
export async function fetchPredictionAccuracyPoints(
  params: PredictionAccuracyPointsParams,
  nowMs = Date.now(),
): Promise<PredictionAccuracyPoints> {
  const url = apiUrl(BTC_PREDICTION_PERFORMANCE_POINTS_PATH)

  if (!url) {
    return simulatePredictionAccuracyPoints(params, nowMs)
  }

  const response = await fetch(
    `${url}?${predictionAccuracyPointsSearchParams(params)}`,
    { headers: { Accept: 'application/json' } },
  )

  if (!response.ok) {
    throw new Error(`Comparison request failed with ${response.status}`)
  }

  return mapPredictionAccuracyPoints(
    (await response.json()) as PerformancePointsResponse,
    params.horizon,
    'live',
  )
}
