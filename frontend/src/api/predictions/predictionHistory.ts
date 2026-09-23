import { BTC_PRICE_HISTORY_PATH } from '@/constants/apiUrls'
import { apiUrl } from '@/lib/apiConfig'
import { HISTORY_WINDOW } from '@/api/predictions/predictionWindow'
import { buildSimulatedHistoryPoints } from '@/api/predictions/simulatedPredictionHistory'
import { simulatedCurrentPrice } from '@/api/predictions/simulatedBtcPrediction'
import type { ChartCandle } from '@/types/chart'
import type {
  PredictionHistory,
  PredictionHistoryParams,
  PredictionHistoryResponse,
  PredictionHorizon,
  PredictionSource,
} from '@/types/predictions'

type PredictionHistoryPoint = PredictionHistoryResponse['points'][number]

const MOCK_LATENCY_MS = 180

export function predictionHistoryQueryKey(params: PredictionHistoryParams) {
  return ['btc-prediction-history', params.range, params.interval] as const
}

export function historyParamsFor(
  horizon: PredictionHorizon,
): PredictionHistoryParams {
  const window = HISTORY_WINDOW[horizon]

  return { horizon, range: window.range, interval: window.interval }
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function mapCandle(point: PredictionHistoryPoint): ChartCandle {
  return {
    time: point.timestamp,
    timeMs: new Date(point.timestamp).getTime(),
    open: point.open,
    high: point.high,
    low: point.low,
    close: point.close,
  }
}

export function mapPredictionHistory(
  response: PredictionHistoryResponse,
  params: PredictionHistoryParams,
  source: PredictionSource = 'live',
): PredictionHistory {
  return {
    source,
    range: params.range,
    interval: params.interval,
    candles: response.points.map(mapCandle),
  }
}

export async function simulatePredictionHistory(
  params: PredictionHistoryParams,
  nowMs = Date.now(),
): Promise<PredictionHistory> {
  await delay(MOCK_LATENCY_MS)

  const points = buildSimulatedHistoryPoints(
    params,
    nowMs,
    simulatedCurrentPrice(nowMs),
  )

  return mapPredictionHistory(
    { range: params.range, interval: params.interval, points },
    params,
    'simulated',
  )
}

/**
 * Actual BTC candles for the window behind a forecast.
 *
 * Unlike the prediction itself, this route *is* proxied by the gateway
 * (`service_proxy.py`), so a full-stack run gets real candles here even while
 * the forecast half falls back. Same contract as everywhere else: no backend
 * configured means simulated data, a configured backend that fails throws.
 */
export async function fetchPredictionHistory(
  params: PredictionHistoryParams,
  nowMs = Date.now(),
): Promise<PredictionHistory> {
  const url = apiUrl(BTC_PRICE_HISTORY_PATH)

  if (!url) {
    return simulatePredictionHistory(params, nowMs)
  }

  const search = new URLSearchParams({
    range: params.range,
    interval: params.interval,
  })

  const response = await fetch(`${url}?${search}`, {
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) {
    throw new Error(`Price history request failed with ${response.status}`)
  }

  return mapPredictionHistory(
    (await response.json()) as PredictionHistoryResponse,
    params,
    'live',
  )
}
