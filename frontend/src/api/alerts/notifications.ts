import axios from 'axios'
import {
  simulateGetNotifications,
  simulateGetUnreadCount,
  simulateMarkAllAsRead,
  simulateMarkAsRead,
} from '@/api/alerts/simulatedNotifications'
import { withSimulatedFallback } from '@/api/alerts/withSimulatedFallback'
import { sortNotificationsByDateNewestFirst } from '@/lib/alerts/sortNotifications'
import { alertApiUrl } from '@/lib/apiConfig'
import type {
  InAppNotification,
  NotificationResponse,
} from '@/types/alerts/notifications'

/** Intended alert-service inbox routes (see NotificationService). */
export const NOTIFICATIONS_PATH = '/api/v1/notifications'

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
      const url = alertApiUrl(NOTIFICATIONS_PATH)
      if (!url) {
        throw new Error('Alert API is not configured')
      }

      const response = await axios.get<NotificationResponse>(url, {
        params: { user_id: userId, ...params },
        headers: JSON_HEADERS,
      })
      return sortedResponse(response.data)
    },
    async () => sortedResponse(await simulateGetNotifications(userId, params)),
  )
}

export async function fetchUnreadNotificationCount(
  userId: string,
): Promise<{ count: number }> {
  return withSimulatedFallback(
    async () => {
      const url = alertApiUrl(`${NOTIFICATIONS_PATH}/unread`)
      if (!url) {
        throw new Error('Alert API is not configured')
      }

      const response = await axios.get<{ count: number }>(url, {
        params: { user_id: userId },
        headers: JSON_HEADERS,
      })
      return response.data
    },
    () => simulateGetUnreadCount(userId),
  )
}

export async function markNotificationAsRead(
  notificationId: string,
): Promise<InAppNotification> {
  return withSimulatedFallback(
    async () => {
      const url = alertApiUrl(`${NOTIFICATIONS_PATH}/${notificationId}/read`)
      if (!url) {
        throw new Error('Alert API is not configured')
      }

      const response = await axios.put<InAppNotification>(url, undefined, {
        headers: JSON_HEADERS,
      })
      return response.data
    },
    () => simulateMarkAsRead(notificationId),
  )
}

export async function markAllNotificationsAsRead(
  userId: string,
): Promise<{ count: number }> {
  return withSimulatedFallback(
    async () => {
      const url = alertApiUrl(`${NOTIFICATIONS_PATH}/read-all`)
      if (!url) {
        throw new Error('Alert API is not configured')
      }

      const response = await axios.post<{ count: number }>(
        url,
        { user_id: userId },
        { headers: JSON_HEADERS },
      )
      return response.data
    },
    () => simulateMarkAllAsRead(userId),
  )
}
