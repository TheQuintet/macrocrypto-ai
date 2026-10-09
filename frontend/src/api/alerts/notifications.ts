import axios from 'axios'
import {
  simulateGetNotifications,
  simulateMarkAllAsRead,
  simulateMarkAsRead,
} from '@/api/alerts/simulatedNotifications'
import { withSimulatedFallback } from '@/api/alerts/withSimulatedFallback'
import { ALERT_NOTIFICATIONS_PATH, NOTIFICATIONS_PATH } from '@/constants/apiUrls'
import { sortNotificationsByDateNewestFirst } from '@/lib/alerts/sortNotifications'
import { apiUrl } from '@/lib/apiConfig'
import type {
  AlertNotificationListResponse,
  InAppNotification,
  MacroNotificationWire,
  NotificationListParams,
  NotificationResponse,
  NotificationSource,
} from '@/types/alerts/notifications'

const NOTIFICATION_SOURCE_PATHS: Record<NotificationSource, string> = {
  macro: NOTIFICATIONS_PATH,
  alerts: ALERT_NOTIFICATIONS_PATH,
}

const NOTIFICATION_SOURCES = Object.keys(
  NOTIFICATION_SOURCE_PATHS,
) as NotificationSource[]

const DEFAULT_LIST_LIMIT = 50

function toInAppNotification(
  raw: MacroNotificationWire,
  source: NotificationSource,
): InAppNotification {
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
    source,
  }
}

const JSON_HEADERS = { Accept: 'application/json' }

export function notificationsQueryKey(userId: string) {
  return ['notifications', userId] as const
}

export function unreadNotificationCountQueryKey(userId: string) {
  return ['notifications', 'unread-count', userId] as const
}

function sortedResponse(response: NotificationResponse): NotificationResponse {
  return {
    ...response,
    notifications: sortNotificationsByDateNewestFirst(
      response.notifications ?? [],
    ),
  }
}

function sourceUrl(source: NotificationSource, suffix = ''): string {
  const url = apiUrl(`${NOTIFICATION_SOURCE_PATHS[source]}${suffix}`)
  if (!url) {
    throw new Error('Alert API is not configured')
  }
  return url
}

/**
 * Run one request per source. A source that fails is skipped so one missing
 * route does not hide the other list; throws only when every source fails.
 */
async function fromEverySource<T>(
  request: (source: NotificationSource) => Promise<T>,
): Promise<T[]> {
  const results = await Promise.allSettled(NOTIFICATION_SOURCES.map(request))
  const values = results.flatMap((result) =>
    result.status === 'fulfilled' ? [result.value] : [],
  )
  if (values.length === 0) {
    throw (results[0] as PromiseRejectedResult).reason
  }
  return values
}

async function fetchSourceNotifications(
  source: NotificationSource,
  params: NotificationListParams,
): Promise<{ total: number; notifications: InAppNotification[] }> {
  const response = await axios.get<AlertNotificationListResponse>(
    sourceUrl(source),
    {
      params: {
        ...(params.limit !== undefined ? { limit: params.limit } : {}),
        ...(params.offset !== undefined ? { offset: params.offset } : {}),
      },
      headers: JSON_HEADERS,
    },
  )
  return {
    total: response.data.total ?? 0,
    notifications: (response.data.notifications ?? []).map((raw) =>
      toInAppNotification(raw, source),
    ),
  }
}

/** Inbox list: macro reminders plus triggered price/prediction alerts. */
export async function fetchNotifications(
  userId: string,
  params: NotificationListParams = {},
): Promise<NotificationResponse> {
  return withSimulatedFallback(
    async () => {
      const lists = await fromEverySource((source) =>
        fetchSourceNotifications(source, params),
      )
      const limit = params.limit ?? DEFAULT_LIST_LIMIT
      const merged = sortNotificationsByDateNewestFirst(
        lists.flatMap((list) => list.notifications),
      )
      return {
        total: lists.reduce((sum, list) => sum + list.total, 0),
        limit,
        offset: params.offset ?? 0,
        notifications: merged.slice(0, limit),
      }
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
  notification: Pick<InAppNotification, 'id' | 'source'>,
): Promise<void> {
  return withSimulatedFallback(
    async () => {
      const url = sourceUrl(
        notification.source ?? 'macro',
        `/${notification.id}/read`,
      )
      await axios.put(url, undefined, { headers: JSON_HEADERS })
    },
    async () => {
      await simulateMarkAsRead(notification.id)
    },
  )
}

export async function markAllNotificationsAsRead(
  userId: string,
): Promise<{ count: number }> {
  return withSimulatedFallback(
    async () => {
      const counts = await fromEverySource(async (source) => {
        const response = await axios.post<{ count?: number }>(
          sourceUrl(source, '/read-all'),
          undefined,
          { headers: JSON_HEADERS },
        )
        return response.data?.count ?? 0
      })
      return { count: counts.reduce((sum, count) => sum + count, 0) }
    },
    () => simulateMarkAllAsRead(userId),
  )
}
