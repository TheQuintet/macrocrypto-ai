import { useNotificationsQuery } from '@/hooks/alerts/useNotificationsQuery'

/** @deprecated The badge counts unread rows on the notification list. */
export const UNREAD_NOTIFICATION_POLL_MS = 30_000

export function useUnreadNotificationCountQuery(userId: string) {
  const query = useNotificationsQuery(userId)
  const count =
    query.data?.notifications.filter((item) => !item.read).length ?? 0

  return {
    ...query,
    data: query.data ? { count } : undefined,
  }
}
