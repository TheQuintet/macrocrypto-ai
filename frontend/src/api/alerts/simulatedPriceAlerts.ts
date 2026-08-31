import { ALERTS_USER_ID } from '@/constants/alerts'
import type {
  CreatePriceAlertRequest,
  PriceAlert,
  PriceAlertHistory,
  PriceAlertListResponse,
  UpdatePriceAlertRequest,
} from '@/types/alerts/priceAlert'

const MOCK_LATENCY_MS = 80

export const simulatedAlertIds = {
  breakout: 'a1111111-1111-4111-8111-111111111111',
  dip: 'a2222222-2222-4222-8222-222222222222',
  roundNumber: 'a3333333-3333-4333-8333-333333333333',
  takeProfit: 'a4444444-4444-4444-8444-444444444444',
  support: 'a5555555-5555-4555-8555-555555555555',
} as const

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function iso(stamp: string) {
  return stamp
}

/** Deterministic seed so a frontend-only run still has alerts to manage. */
export function buildSimulatedPriceAlerts(userId = ALERTS_USER_ID): PriceAlert[] {
  return [
    {
      id: simulatedAlertIds.breakout,
      user_id: userId,
      threshold_price: 70_000,
      alert_type: 'crosses_above',
      asset: 'BTC/USD',
      status: 'active',
      one_time: false,
      created_at: iso('2026-08-20T09:00:00.000Z'),
      updated_at: iso('2026-08-28T11:20:00.000Z'),
      triggered_at: null,
      notify_in_app: true,
      notify_email: true,
      name: 'BTC breakout',
      description: 'Catch a move through 70k',
    },
    {
      id: simulatedAlertIds.dip,
      user_id: userId,
      threshold_price: 60_000,
      alert_type: 'crosses_below',
      asset: 'BTC/USD',
      status: 'active',
      one_time: false,
      created_at: iso('2026-08-21T14:00:00.000Z'),
      updated_at: iso('2026-08-21T14:00:00.000Z'),
      triggered_at: null,
      notify_in_app: true,
      notify_email: false,
      name: 'Buy the dip',
      description: null,
    },
    {
      id: simulatedAlertIds.roundNumber,
      user_id: userId,
      threshold_price: 65_000,
      alert_type: 'reaches',
      asset: 'BTC/USD',
      status: 'active',
      one_time: true,
      created_at: iso('2026-08-22T08:30:00.000Z'),
      updated_at: iso('2026-08-22T08:30:00.000Z'),
      triggered_at: null,
      notify_in_app: true,
      notify_email: false,
      name: null,
      description: null,
    },
    {
      id: simulatedAlertIds.takeProfit,
      user_id: userId,
      threshold_price: 80_000,
      alert_type: 'crosses_above',
      asset: 'BTC/USD',
      status: 'disabled',
      one_time: true,
      created_at: iso('2026-08-18T16:45:00.000Z'),
      updated_at: iso('2026-08-29T10:00:00.000Z'),
      triggered_at: null,
      notify_in_app: true,
      notify_email: true,
      name: 'Take profit',
      description: 'Paused until the next rally',
    },
    {
      id: simulatedAlertIds.support,
      user_id: userId,
      threshold_price: 55_000,
      alert_type: 'crosses_below',
      asset: 'BTC/USD',
      status: 'disabled',
      one_time: false,
      created_at: iso('2026-08-12T12:00:00.000Z'),
      updated_at: iso('2026-08-27T09:15:00.000Z'),
      triggered_at: null,
      notify_in_app: true,
      notify_email: false,
      name: null,
      description: 'Old support level',
    },
  ]
}

function buildSeedHistory(): PriceAlertHistory[] {
  return [
    {
      id: 'h1111111-1111-4111-8111-111111111111',
      alert_id: simulatedAlertIds.breakout,
      event_type: 'triggered',
      event_source: 'simulated',
      triggered_price: 70_120,
      threshold_price: 70_000,
      alert_type: 'crosses_above',
      previous_status: 'active',
      new_status: 'active',
      triggered_at: iso('2026-08-25T13:42:00.000Z'),
      created_at: iso('2026-08-25T13:42:00.000Z'),
    },
  ]
}

let alerts = buildSimulatedPriceAlerts()
let history = buildSeedHistory()

export function resetSimulatedPriceAlerts() {
  alerts = buildSimulatedPriceAlerts()
  history = buildSeedHistory()
}

function requireAlert(alertId: string) {
  const alert = alerts.find((item) => item.id === alertId)
  if (!alert) {
    throw new Error(`Alert ${alertId} was not found`)
  }
  return alert
}

export async function simulateGetAlerts(
  userId: string,
  params?: { status?: string; alert_type?: string; limit?: number; offset?: number },
): Promise<PriceAlertListResponse> {
  await delay(MOCK_LATENCY_MS)

  let list = alerts.filter((alert) => alert.user_id === userId)
  if (params?.status) {
    list = list.filter((alert) => alert.status === params.status)
  }
  if (params?.alert_type) {
    list = list.filter((alert) => alert.alert_type === params.alert_type)
  }

  const offset = params?.offset ?? 0
  const limit = params?.limit ?? 50

  return {
    total: list.length,
    limit,
    offset,
    alerts: list.slice(offset, offset + limit),
  }
}

export async function simulateGetAlert(alertId: string): Promise<PriceAlert> {
  await delay(MOCK_LATENCY_MS)
  return { ...requireAlert(alertId) }
}

export async function simulateCreateAlert(
  data: CreatePriceAlertRequest,
): Promise<PriceAlert> {
  await delay(MOCK_LATENCY_MS)

  const now = new Date().toISOString()
  const created: PriceAlert = {
    id: crypto.randomUUID(),
    user_id: data.user_id,
    threshold_price: data.threshold_price,
    alert_type: data.alert_type,
    asset: data.asset ?? 'BTC/USD',
    status: 'active',
    one_time: data.one_time ?? true,
    created_at: now,
    updated_at: now,
    triggered_at: null,
    notify_in_app: data.notify_in_app ?? true,
    notify_email: data.notify_email ?? false,
    name: data.name?.trim() ? data.name : null,
    description: data.description?.trim() ? data.description : null,
  }

  alerts = [created, ...alerts]
  return { ...created }
}

export async function simulateUpdateAlert(
  alertId: string,
  data: UpdatePriceAlertRequest,
): Promise<PriceAlert> {
  await delay(MOCK_LATENCY_MS)

  const current = requireAlert(alertId)
  const updated: PriceAlert = {
    ...current,
    ...data,
    name: data.name === undefined ? current.name : data.name.trim() ? data.name : null,
    description:
      data.description === undefined
        ? current.description
        : data.description.trim()
          ? data.description
          : null,
    updated_at: new Date().toISOString(),
  }

  alerts = alerts.map((alert) => (alert.id === alertId ? updated : alert))
  return { ...updated }
}

export async function simulateDeleteAlert(alertId: string): Promise<void> {
  await delay(MOCK_LATENCY_MS)
  requireAlert(alertId)
  alerts = alerts.filter((alert) => alert.id !== alertId)
  history = history.filter((event) => event.alert_id !== alertId)
}

export async function simulateTriggerAlert(alertId: string): Promise<PriceAlert> {
  await delay(MOCK_LATENCY_MS)

  const current = requireAlert(alertId)
  const now = new Date().toISOString()
  const triggered: PriceAlert = {
    ...current,
    status: current.one_time ? 'triggered' : current.status,
    triggered_at: now,
    updated_at: now,
  }

  alerts = alerts.map((alert) => (alert.id === alertId ? triggered : alert))
  history = [
    {
      id: crypto.randomUUID(),
      alert_id: alertId,
      event_type: 'triggered',
      event_source: 'simulated',
      triggered_price: current.threshold_price,
      threshold_price: current.threshold_price,
      alert_type: current.alert_type,
      previous_status: current.status,
      new_status: triggered.status,
      triggered_at: now,
      created_at: now,
    },
    ...history,
  ]

  return { ...triggered }
}

export async function simulateGetHistory(
  alertId: string,
  params?: { limit?: number; offset?: number },
): Promise<{ history: PriceAlertHistory[]; total: number }> {
  await delay(MOCK_LATENCY_MS)
  requireAlert(alertId)

  const events = history.filter((event) => event.alert_id === alertId)
  const offset = params?.offset ?? 0
  const limit = params?.limit ?? 50

  return {
    total: events.length,
    history: events.slice(offset, offset + limit),
  }
}
