import axios from 'axios'
import {
  simulateGetNotifications,
  simulateMarkAllAsRead,
  simulateMarkAsRead,
} from '@/api/alerts/simulatedNotifications'
import { withSimulatedFallback } from '@/api/alerts/withSimulatedFallback'
import { NOTIFICATIONS_PATH } from '@/constants/apiUrls'
import { sortNotificationsByDateNewestFirst } from '@/lib/alerts/sortNotifications'
import { apiUrl } from '@/lib/apiConfig'
import type {
  InAppNotification,
  NotificationResponse,
  NotificationType,
} from '@/types/alerts/notifications'

/** Gateway list item from GET /api/v1/macro/notifications. */
type MacroNotificationWire = {
  id: string
  user_id?: string
  alert_id?: string | null
  event_name?: string
  description?: string | null
  data?: Record<string, unknown> | null
  action_url?: string | null
  read?: boolean
  is_archived?: boolean
  sent_at?: string | null
  read_at?: string | null
  title?: string
  message?: string
  notification_type?: NotificationType
  created_at?: string
}

function toInAppNotification(raw: MacroNotificationWire): InAppNotification {
  return {
    id: raw.id,
    user_id: raw.user_id ?? '',
    alert_id: raw.alert_id ?? null,
    title: raw.title ?? raw.event_name ?? 'Macro alert',
    message: raw.message ?? raw.description ?? '',
    notification_type: raw.notification_type ?? 'macro_alert',
    data: raw.data ?? null,
    action_url: raw.action_url ?? null,
    read: Boolean(raw.read),
    is_archived: Boolean(raw.is_archived),
    created_at: raw.created_at ?? raw.sent_at ?? '',
    read_at: raw.read_at ?? null,
  }
}

const JSON_HEADERS = { Accept: 'application/json' }

export function notificationsQueryKey(userId: string) {
  return ['notifications', userId] as const
}

export function unreadNotificationCountQueryKey(userId: string) {
  return ['notifications', 'unread-count', userId] as const
}

type NotificationListParams = {
  unread_only?: boolean
  limit?: number
  offset?: number
}

function sortedResponse(response: NotificationResponse): NotificationResponse {
  return {
    ...response,
    notifications: sortNotificationsByDateNewestFirst(
      response.notifications ?? [],
    ),
  }
}

export async function fetchNotifications(
  userId: string,
  params: NotificationListParams = {},
): Promise<NotificationResponse> {
  return withSimulatedFallback(
    async () => {
      const url = apiUrl(NOTIFICATIONS_PATH)
      if (!url) {
        throw new Error('Alert API is not configured')
      }

      const response = await axios.get<{
        total: number
        limit: number
        offset: number
        notifications: MacroNotificationWire[]
      }>(url, {
        params: {
          ...(params.limit !== undefined ? { limit: params.limit } : {}),
          ...(params.offset !== undefined ? { offset: params.offset } : {}),
        },
        headers: JSON_HEADERS,
      })
      return sortedResponse({
        ...response.data,
        notifications: (response.data.notifications ?? []).map(
          toInAppNotification,
        ),
      })
    },
    async () => sortedResponse(await simulateGetNotifications(userId, params)),
  )
}

export async function fetchUnreadNotificationCount(
  userId: string,
): Promise<{ count: number }> {
  const list = await fetchNotifications(userId)
  return {
    count: list.notifications.filter((item) => !item.read).length,
  }
}

export async function markNotificationAsRead(
  notificationId: string,
): Promise<void> {
  return withSimulatedFallback(
    async () => {
      const url = apiUrl(`${NOTIFICATIONS_PATH}/${notificationId}/read`)
      if (!url) {
        throw new Error('Alert API is not configured')
      }

      await axios.put(url, undefined, { headers: JSON_HEADERS })
    },
    async () => {
      await simulateMarkAsRead(notificationId)
    },
  )
}

export async function markAllNotificationsAsRead(
  userId: string,
): Promise<{ count: number }> {
  return withSimulatedFallback(
    async () => {
      const url = apiUrl(`${NOTIFICATIONS_PATH}/read-all`)
      if (!url) {
        throw new Error('Alert API is not configured')
      }

      const response = await axios.post<{ count: number }>(url, undefined, {
        headers: JSON_HEADERS,
      })
      return response.data
    },
    () => simulateMarkAllAsRead(userId),
  )
}
