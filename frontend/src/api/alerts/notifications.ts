import axios from 'axios'
import {
  simulateGetNotifications,
  simulateMarkAllAsRead,
  simulateMarkAsRead,
} from '@/api/alerts/simulatedNotifications'
import { withSimulatedFallback } from '@/api/alerts/withSimulatedFallback'
import { ALERT_NOTIFICATIONS_PATH, NOTIFICATIONS_PATH } from '@/constants/apiUrls'
import { sortNotificationsByDateNewestFirst } from '@/lib/alerts/sortNotifications'
import { asUtcTimestamp } from '@/lib/alerts/utcTimestamp'
import { apiUrl, isApiGatewayConfigured } from '@/lib/apiConfig'
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
    created_at: asUtcTimestamp(raw.created_at ?? raw.sent_at ?? ''),
    read_at: raw.read_at ? asUtcTimestamp(raw.read_at) : null,
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

/**
 * Read updates are live-only once the gateway is set: a failure must reach the
 * mutation instead of a simulated success that marks the row read in the UI.
 */
async function liveOrSimulated<T>(
  live: () => Promise<T>,
  simulate: () => Promise<T>,
): Promise<T> {
  return isApiGatewayConfigured() ? live() : simulate()
}

/**
 * List a row belongs to. Rows without `source` (e.g. from the stream) follow
 * the backend split: macro reminders vs. price/prediction triggers.
 */
export function notificationSource(
  notification: Pick<InAppNotification, 'source' | 'notification_type'>,
): NotificationSource {
  if (notification.source) return notification.source
  return notification.notification_type === 'macro_alert' ? 'macro' : 'alerts'
}

async function fetchSourceNotifications(
  source: NotificationSource,
  limit: number,
): Promise<{ total: number; notifications: InAppNotification[] }> {
  const response = await axios.get<AlertNotificationListResponse>(
    sourceUrl(source),
    {
      params: { limit },
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
      // Each source is paged on its own, so a merged page at `offset` needs
      // every source's first `offset + limit` rows, sliced after the merge.
      const limit = params.limit ?? DEFAULT_LIST_LIMIT
      const offset = params.offset ?? 0
      const lists = await fromEverySource((source) =>
        fetchSourceNotifications(source, offset + limit),
      )
      const merged = sortNotificationsByDateNewestFirst(
        lists.flatMap((list) => list.notifications),
      )
      return {
        total: lists.reduce((sum, list) => sum + list.total, 0),
        limit,
        offset,
        notifications: merged.slice(offset, offset + limit),
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
  notification: Pick<InAppNotification, 'id' | 'source' | 'notification_type'>,
): Promise<void> {
  return liveOrSimulated(
    async () => {
      const url = sourceUrl(
        notificationSource(notification),
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
  return liveOrSimulated(
    async () => {
      // Every list must succeed: the caller marks all cached rows read.
      const counts = await Promise.all(
        NOTIFICATION_SOURCES.map(async (source) => {
          const response = await axios.post<{ count?: number }>(
            sourceUrl(source, '/read-all'),
            undefined,
            { headers: JSON_HEADERS },
          )
          return response.data?.count ?? 0
        }),
      )
      return { count: counts.reduce((sum, count) => sum + count, 0) }
    },
    () => simulateMarkAllAsRead(userId),
  )
}
