import { sortNotificationsByDateNewestFirst } from '@/lib/alerts/sortNotifications'
import type {
  InAppNotification,
  NotificationResponse,
} from '@/types/alerts/notifications'

const DEFAULT_PAGE = { total: 0, limit: 50, offset: 0 } as const

export function mergeIncomingNotification(
  current: NotificationResponse | undefined,
  incoming: InAppNotification,
): NotificationResponse {
  const existing = current?.notifications ?? []
  const alreadyKnown = existing.some((item) => item.id === incoming.id)
  const notifications = sortNotificationsByDateNewestFirst(
    alreadyKnown
      ? existing.map((item) => (item.id === incoming.id ? incoming : item))
      : [incoming, ...existing],
  )

  return {
    total: alreadyKnown
      ? (current?.total ?? existing.length)
      : (current?.total ?? existing.length) + 1,
    limit: current?.limit ?? DEFAULT_PAGE.limit,
    offset: current?.offset ?? DEFAULT_PAGE.offset,
    notifications,
  }
}

export function unreadCountAfterIncoming(
  currentCount: number | undefined,
  incoming: InAppNotification,
  alreadyKnown: boolean,
): number {
  if (alreadyKnown || incoming.read) return currentCount ?? 0
  return (currentCount ?? 0) + 1
}

export function listContainsNotification(
  current: NotificationResponse | undefined,
  notificationId: string,
): boolean {
  return current?.notifications.some((item) => item.id === notificationId) ?? false
}
