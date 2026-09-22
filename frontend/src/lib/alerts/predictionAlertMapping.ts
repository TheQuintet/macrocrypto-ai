import { resolveAlertStatus } from '@/components/alerts/shared/alertStatus'
import type {
  CreatePredictionAlertRequest,
  PredictionAlert,
  PredictionAlertApiRecord,
  PredictionDirection,
  PredictionHorizon,
  PredictionThreshold,
  UpdatePredictionAlertRequest,
} from '@/types/alerts/predictionAlert'

const HORIZONS: PredictionHorizon[] = ['24h', '7d']
const DIRECTIONS: PredictionDirection[] = ['up', 'down', 'both']
const THRESHOLDS: PredictionThreshold[] = [1, 2, 5, 10]

export const DEFAULT_PREDICTION_ASSET = 'BTC/USD'
export const DEFAULT_PREDICTION_DIRECTION: PredictionDirection = 'both'

export function toUiHorizon(value: string | null | undefined): PredictionHorizon {
  return HORIZONS.includes(value as PredictionHorizon) ? (value as PredictionHorizon) : '24h'
}

export function toUiDirection(value: string | null | undefined): PredictionDirection {
  return DIRECTIONS.includes(value as PredictionDirection)
    ? (value as PredictionDirection)
    : DEFAULT_PREDICTION_DIRECTION
}

/** Snap a backend float (1–10) onto the UI select options. */
export function toUiThreshold(value: number): PredictionThreshold {
  return THRESHOLDS.reduce((closest, option) =>
    Math.abs(option - value) < Math.abs(closest - value) ? option : closest,
  )
}

export function toCreateApiPayload(data: CreatePredictionAlertRequest) {
  return {
    user_id: data.user_id,
    threshold_percent: data.threshold,
    horizon: data.horizon,
    direction: data.direction ?? DEFAULT_PREDICTION_DIRECTION,
    asset: DEFAULT_PREDICTION_ASSET,
    monitor_confidence: true,
    confidence_threshold_percent: data.confidence_change,
    name: data.name || null,
    description: data.description || null,
    notify_in_app: data.notify_in_app,
    notify_email: data.notify_email,
  }
}

export function toUpdateApiPayload(data: UpdatePredictionAlertRequest) {
  const payload: Record<string, unknown> = {}
  if (data.threshold != null) payload.threshold_percent = data.threshold
  if (data.horizon != null) payload.horizon = data.horizon
  if (data.direction != null) payload.direction = data.direction
  if (data.confidence_change != null) {
    payload.confidence_threshold_percent = data.confidence_change
  }
  if (data.name !== undefined) payload.name = data.name || null
  if (data.description !== undefined) payload.description = data.description || null
  if (data.notify_in_app != null) payload.notify_in_app = data.notify_in_app
  if (data.notify_email != null) payload.notify_email = data.notify_email
  if (data.status != null && data.status !== 'triggered') payload.status = data.status
  return payload
}

export function toUiAlert(row: PredictionAlertApiRecord): PredictionAlert | null {
  if (!row.id || !row.user_id) return null

  const status = resolveAlertStatus(row.status) ?? 'active'

  return {
    id: row.id,
    user_id: row.user_id,
    threshold: toUiThreshold(Number(row.threshold_percent)),
    horizon: toUiHorizon(row.horizon),
    confidence_change: Number(row.confidence_threshold_percent) || 0,
    direction: toUiDirection(row.direction),
    asset: row.asset || DEFAULT_PREDICTION_ASSET,
    status,
    one_time: false,
    name: row.name ?? undefined,
    description: row.description ?? undefined,
    notify_in_app: Boolean(row.notify_in_app),
    notify_email: Boolean(row.notify_email),
    created_at: row.created_at,
    updated_at: row.updated_at,
    triggered_at: row.triggered_at,
  }
}
