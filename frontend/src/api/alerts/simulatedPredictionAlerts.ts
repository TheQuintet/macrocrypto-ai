import { ALERTS_USER_ID } from '@/constants/alerts'
import { getRecommendation } from '@/components/alerts/prediction/predictionAlertRule'
import type {
  CreatePredictionAlertRequest,
  PredictionAlert,
  PredictionAlertHistory,
  PredictionAlertPreview,
  PredictionHorizon,
  PredictionThreshold,
  UpdatePredictionAlertRequest,
} from '@/types/alerts/predictionAlert'

const MOCK_LATENCY_MS = 80

export const simulatedPredictionAlertIds = {
  breakout: 'p1111111-1111-4111-8111-111111111111',
  major: 'p2222222-2222-4222-8222-222222222222',
  minor: 'p3333333-3333-4333-8333-333333333333',
} as const

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export function buildSimulatedPredictionAlerts(
  userId = ALERTS_USER_ID,
): PredictionAlert[] {
  const now = '2026-08-28T11:20:00.000Z'
  return [
    {
      id: simulatedPredictionAlertIds.breakout,
      user_id: userId,
      threshold: 5,
      horizon: '24h',
      confidence_change: 5,
      direction: 'both',
      asset: 'BTC/USD',
      status: 'active',
      one_time: false,
      name: 'Bullish Breakout Alert',
      description: 'Get notified when prediction shows strong upward movement',
      notify_in_app: true,
      notify_email: false,
      created_at: '2026-08-20T09:00:00.000Z',
      updated_at: now,
    },
    {
      id: simulatedPredictionAlertIds.major,
      user_id: userId,
      threshold: 10,
      horizon: '7d',
      confidence_change: 8,
      direction: 'both',
      asset: 'BTC/USD',
      status: 'active',
      one_time: true,
      name: 'Major Trend Change',
      description: 'Alert for significant 7-day prediction changes',
      notify_in_app: true,
      notify_email: true,
      created_at: '2026-08-21T09:00:00.000Z',
      updated_at: now,
    },
    {
      id: simulatedPredictionAlertIds.minor,
      user_id: userId,
      threshold: 2,
      horizon: '24h',
      confidence_change: 3,
      direction: 'both',
      asset: 'BTC/USD',
      status: 'disabled',
      one_time: false,
      name: 'Minor Shifts',
      description: 'Get notified about small but frequent changes',
      notify_in_app: true,
      notify_email: false,
      created_at: '2026-08-22T09:00:00.000Z',
      updated_at: now,
    },
  ]
}

function buildSimulatedHistory(): PredictionAlertHistory[] {
  return [
    {
      id: 'h1111111-1111-4111-8111-111111111111',
      alert_id: simulatedPredictionAlertIds.breakout,
      previous_prediction: 68234.5,
      new_prediction: 70123.75,
      change_percentage: 2.77,
      horizon: '24h',
      threshold: 5,
      triggered_at: '2026-08-28T10:20:00.000Z',
      recommendation: 'Bullish shift - consider increasing exposure',
      read: false,
    },
    {
      id: 'h2222222-2222-4222-8222-222222222222',
      alert_id: simulatedPredictionAlertIds.major,
      previous_prediction: 71500,
      new_prediction: 68900,
      change_percentage: -3.64,
      horizon: '7d',
      threshold: 10,
      triggered_at: '2026-08-28T09:20:00.000Z',
      recommendation: 'Bearish shift - consider adjusting position',
      read: true,
    },
  ]
}

let alerts = buildSimulatedPredictionAlerts()
const history = buildSimulatedHistory()

export function resetSimulatedPredictionAlerts() {
  alerts = buildSimulatedPredictionAlerts()
}

export async function simulateGetAlerts(userId: string): Promise<PredictionAlert[]> {
  await delay(MOCK_LATENCY_MS)
  return alerts.filter((alert) => alert.user_id === userId)
}

export async function simulateCreateAlert(
  data: CreatePredictionAlertRequest,
): Promise<PredictionAlert> {
  await delay(MOCK_LATENCY_MS)
  const created: PredictionAlert = {
    id: crypto.randomUUID(),
    ...data,
    direction: data.direction ?? 'both',
    asset: 'BTC/USD',
    status: 'active',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
  alerts = [...alerts, created]
  return created
}

export async function simulateUpdateAlert(
  alertId: string,
  data: UpdatePredictionAlertRequest,
): Promise<PredictionAlert> {
  await delay(MOCK_LATENCY_MS)
  const index = alerts.findIndex((alert) => alert.id === alertId)
  if (index === -1) throw new Error('Alert not found')
  const updated: PredictionAlert = {
    ...alerts[index],
    ...data,
    updated_at: new Date().toISOString(),
  }
  alerts = alerts.map((alert, i) => (i === index ? updated : alert))
  return updated
}

export async function simulateDeleteAlert(alertId: string): Promise<void> {
  await delay(MOCK_LATENCY_MS)
  alerts = alerts.filter((alert) => alert.id !== alertId)
}

export async function simulateToggleStatus(alertId: string): Promise<PredictionAlert> {
  const current = alerts.find((alert) => alert.id === alertId)
  if (!current) throw new Error('Alert not found')
  const status = current.status === 'active' || current.status === 'triggered'
    ? 'disabled'
    : 'active'
  return simulateUpdateAlert(alertId, { status })
}

export type HistoryQuery = {
  startDate?: string
  endDate?: string
  horizon?: PredictionHorizon
  threshold?: PredictionThreshold
  search?: string
  page?: number
  limit?: number
}

export async function simulateGetHistory(
  userId: string,
  params?: HistoryQuery,
): Promise<{
  history: PredictionAlertHistory[]
  total: number
  page: number
  totalPages: number
}> {
  await delay(MOCK_LATENCY_MS)
  void userId
  let filtered = [...history]
  if (params?.horizon) {
    filtered = filtered.filter((row) => row.horizon === params.horizon)
  }
  if (params?.threshold) {
    filtered = filtered.filter((row) => row.threshold === params.threshold)
  }
  if (params?.search) {
    const search = params.search.toLowerCase()
    filtered = filtered.filter((row) =>
      row.recommendation.toLowerCase().includes(search),
    )
  }
  if (params?.startDate) {
    filtered = filtered.filter(
      (row) => new Date(row.triggered_at) >= new Date(params.startDate!),
    )
  }
  if (params?.endDate) {
    filtered = filtered.filter(
      (row) => new Date(row.triggered_at) <= new Date(params.endDate!),
    )
  }

  const page = params?.page || 1
  const limit = params?.limit || 10
  const start = (page - 1) * limit
  return {
    history: filtered.slice(start, start + limit),
    total: filtered.length,
    page,
    totalPages: Math.max(1, Math.ceil(filtered.length / limit)),
  }
}

export async function simulateExportHistory(
  userId: string,
  params?: { startDate?: string; endDate?: string; horizon?: PredictionHorizon },
): Promise<Blob> {
  const { history: rows } = await simulateGetHistory(userId, params)
  const header =
    'Previous Prediction,New Prediction,Change %,Horizon,Threshold,Recommendation,Triggered At'
  const body = rows.map((row) =>
    [
      row.previous_prediction,
      row.new_prediction,
      row.change_percentage,
      row.horizon,
      row.threshold,
      `"${row.recommendation.replaceAll('"', '""')}"`,
      row.triggered_at,
    ].join(','),
  )
  return new Blob([[header, ...body].join('\n')], { type: 'text/csv' })
}

export function buildSimulatedPreview(
  data: CreatePredictionAlertRequest,
): PredictionAlertPreview {
  const previousPrediction = 68234.5
  const changePercentage = data.threshold
  const newPrediction =
    previousPrediction * (1 + changePercentage / 100)
  return {
    previousPrediction,
    newPrediction,
    changePercentage,
    confidence: 70,
    recommendation: getRecommendation(previousPrediction, newPrediction),
    horizon: data.horizon,
  }
}

export async function simulateGetPreview(
  data: CreatePredictionAlertRequest,
): Promise<PredictionAlertPreview> {
  await delay(MOCK_LATENCY_MS)
  return buildSimulatedPreview(data)
}
