import { simulatedAlertIds } from '@/api/alerts/simulatedPriceAlerts'
import { ALERTS_USER_ID } from '@/constants/alerts'
import { routes } from '@/constants/navigation'
import type { InAppNotification, NotificationResponse } from '@/types/alerts/priceAlert'

const MOCK_LATENCY_MS = 80

export const simulatedNotificationIds = {
  breakout: 'n1111111-1111-4111-8111-111111111111',
  roundNumber: 'n2222222-2222-4222-8222-222222222222',
  dip: 'n3333333-3333-4333-8333-333333333333',
  forecast: 'n4444444-4444-4444-8444-444444444444',
} as const

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/** Deterministic seed so the bell has something to show without a backend. */
export function buildSimulatedNotifications(
  userId = ALERTS_USER_ID,
): InAppNotification[] {
  return [
    {
      id: simulatedNotificationIds.breakout,
      user_id: userId,
      alert_id: simulatedAlertIds.breakout,
      title: 'BTC broke $70,000',
      message: 'BTC/USD went above $70,000.00',
      notification_type: 'price_alert',
      data: { threshold_price: 70_000, triggered_price: 70_120 },
      action_url: routes.alerts,
      read: false,
      is_archived: false,
      created_at: '2026-08-30T10:05:00.000Z',
      read_at: null,
    },
    {
      id: simulatedNotificationIds.roundNumber,
      user_id: userId,
      alert_id: simulatedAlertIds.roundNumber,
      title: 'BTC hit $65,000',
      message: 'BTC/USD hits $65,000.00',
      notification_type: 'price_alert',
      data: { threshold_price: 65_000, triggered_price: 65_000 },
      action_url: routes.alerts,
      read: false,
      is_archived: false,
      created_at: '2026-08-30T08:20:00.000Z',
      read_at: null,
    },
    {
      id: simulatedNotificationIds.dip,
      user_id: userId,
      alert_id: simulatedAlertIds.dip,
      title: 'BTC dipped under $60,000',
      message: 'BTC/USD went below $60,000.00',
      notification_type: 'price_alert',
      data: { threshold_price: 60_000, triggered_price: 59_840 },
      action_url: routes.alerts,
      read: true,
      is_archived: false,
      created_at: '2026-08-29T16:12:00.000Z',
      read_at: '2026-08-29T16:18:00.000Z',
    },
    {
      id: simulatedNotificationIds.forecast,
      user_id: userId,
      alert_id: null,
      title: '24h outlook updated',
      message: 'The model is leaning slightly bullish for the next 24 hours.',
      notification_type: 'prediction_alert',
      data: null,
      action_url: routes.forecasts,
      read: true,
      is_archived: false,
      created_at: '2026-08-28T12:00:00.000Z',
      read_at: '2026-08-28T12:40:00.000Z',
    },
  ]
}

let notifications = buildSimulatedNotifications()

export function resetSimulatedNotifications() {
  notifications = buildSimulatedNotifications()
}

function requireNotification(notificationId: string) {
  const notification = notifications.find((item) => item.id === notificationId)
  if (!notification) {
    throw new Error(`Notification ${notificationId} was not found`)
  }
  return notification
}

export async function simulateGetNotifications(
  userId: string,
  params?: { unread_only?: boolean; limit?: number; offset?: number },
): Promise<NotificationResponse> {
  await delay(MOCK_LATENCY_MS)

  let list = notifications.filter((item) => item.user_id === userId)
  if (params?.unread_only) {
    list = list.filter((item) => !item.read)
  }

  const offset = params?.offset ?? 0
  const limit = params?.limit ?? 50

  return {
    total: list.length,
    limit,
    offset,
    notifications: list.slice(offset, offset + limit),
  }
}

export async function simulateGetUnreadCount(
  userId: string,
): Promise<{ count: number }> {
  await delay(MOCK_LATENCY_MS)
  return {
    count: notifications.filter((item) => item.user_id === userId && !item.read)
      .length,
  }
}

export async function simulateMarkAsRead(
  notificationId: string,
): Promise<InAppNotification> {
  await delay(MOCK_LATENCY_MS)

  const current = requireNotification(notificationId)
  const updated: InAppNotification = {
    ...current,
    read: true,
    read_at: current.read_at ?? new Date().toISOString(),
  }

  notifications = notifications.map((item) =>
    item.id === notificationId ? updated : item,
  )
  return { ...updated }
}

export async function simulateMarkAllAsRead(
  userId: string,
): Promise<{ count: number }> {
  await delay(MOCK_LATENCY_MS)

  const now = new Date().toISOString()
  let count = 0
  notifications = notifications.map((item) => {
    if (item.user_id !== userId || item.read) return item
    count += 1
    return { ...item, read: true, read_at: now }
  })

  return { count }
}
