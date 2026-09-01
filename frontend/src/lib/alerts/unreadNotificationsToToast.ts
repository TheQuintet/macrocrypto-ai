import type { InAppNotification } from '@/types/alerts/notifications'

/** Unread inbox items, oldest first, so the newest toast ends up on top. */
export function unreadNotificationsToToast(
  notifications: InAppNotification[] | undefined,
): InAppNotification[] {
  if (!notifications?.length) return []
  return [...notifications.filter((item) => !item.read)].reverse()
}
