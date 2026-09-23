import type { InAppNotification } from '@/types/alerts/notifications'

/** Newest `created_at` first. Equal timestamps keep a stable id order. */
export function sortNotificationsByDateNewestFirst(
  notifications: InAppNotification[],
): InAppNotification[] {
  return [...notifications].sort((left, right) => {
    const byDate =
      Date.parse(right.created_at) - Date.parse(left.created_at)
    if (byDate !== 0) return byDate
    return right.id.localeCompare(left.id)
  })
}

/** Split a newest-first list so unread rows can sit above read ones. */
export function splitNotificationsByRead(notifications: InAppNotification[]) {
  return {
    unread: notifications.filter((notification) => !notification.read),
    read: notifications.filter((notification) => notification.read),
  }
}
