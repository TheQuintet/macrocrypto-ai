import { apiUrl } from '@/lib/apiConfig'
import { buildSimulatedPrediction } from '@/api/predictions/simulatedBtcPrediction'
import type {
  BtcPrediction,
  PredictionHorizon,
  PredictionParams,
  PredictionPoint,
  PredictionPointResponse,
  PredictionResponse,
  PredictionSource,
} from '@/types/predictions'

/** Real endpoint on the ai-service (see `app/api/v1/predict.py`). */
export const BTC_PREDICTION_PATH = '/api/v1/predict/btc'

/** Predictions are cached for 5 minutes upstream; match that here. */
export const PREDICTION_STALE_MS = 5 * 60 * 1000

const MOCK_LATENCY_MS = 220

export function btcPredictionQueryKey(params: PredictionParams) {
  return ['btc-prediction', params.horizon, params.confidence] as const
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * Query string for a single-model batch.
 *
 * `models` is deliberately absent: naming two or more models switches the
 * endpoint to a `ComparisonResponse` envelope, which is a different shape
 * from the one this screen renders.
 */
export function btcPredictionSearchParams(params: PredictionParams) {
  return new URLSearchParams({
    horizon: params.horizon,
    confidence: String(params.confidence),
  })
}

function mapPoint(point: PredictionPointResponse): PredictionPoint {
  return {
    time: point.time,
    timeMs: new Date(point.time).getTime(),
    predictedPrice: point.predicted_price,
    lowerBound: point.lower_bound,
    upperBound: point.upper_bound,
  }
}

/** Wire -> UI mapping; the only piece the live endpoint landing has to keep. */
export function mapBtcPrediction(
  response: PredictionResponse,
  source: PredictionSource = 'live',
): BtcPrediction {
  return {
    source,
    horizon: response.horizon as PredictionHorizon,
    modelName: response.model_name,
    confidence: response.confidence,
    predictionTime: response.prediction_time,
    currentPrice: response.current_price,
    predictedEndPrice: response.predicted_end_price,
    priceChangePct: response.price_change_pct,
    trend: response.trend,
    points: response.predictions.map(mapPoint),
  }
}

/** Stand-in batch for a frontend-only run, labelled as simulated. */
export async function simulateBtcPrediction(
  params: PredictionParams,
  nowMs = Date.now(),
): Promise<BtcPrediction> {
  await delay(MOCK_LATENCY_MS)

  return mapBtcPrediction(buildSimulatedPrediction(params, nowMs), 'simulated')
}

/**
 * Latest BTC prediction batch from the ai-service.
 *
 * With no backend configured the screen runs on simulated data so it still
 * works standalone. When a backend *is* configured a failed request throws
 * rather than quietly substituting invented forecasts — an error state is the
 * honest answer, and fake bounds under a "Live" reading would not be.
 *
 * Note: the API gateway does not yet proxy the ai-service, so a full-stack run
 * currently 404s here and surfaces that error state. Routing it is a backend
 * task; nothing on this path changes when it lands.
 */
export async function fetchBtcPrediction(
  params: PredictionParams,
  nowMs = Date.now(),
): Promise<BtcPrediction> {
  const url = apiUrl(BTC_PREDICTION_PATH)

  if (!url) {
    return simulateBtcPrediction(params, nowMs)
  }

  const response = await fetch(`${url}?${btcPredictionSearchParams(params)}`, {
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) {
    throw new Error(`Prediction request failed with ${response.status}`)
  }

  return mapBtcPrediction((await response.json()) as PredictionResponse, 'live')
}
