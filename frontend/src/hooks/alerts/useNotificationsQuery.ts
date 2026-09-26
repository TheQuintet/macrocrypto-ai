import { useQuery } from '@tanstack/react-query'
import {
  fetchNotifications,
  notificationsQueryKey,
} from '@/api/alerts/notifications'
import { useNotificationStreamStore } from '@/stores/notificationStreamStore'
import type { NotificationResponse } from '@/types/alerts/notifications'

/** List poll while no live stream is connected. */
export const NOTIFICATION_LIST_POLL_MS = 30_000

export function useNotificationsQuery(
  userId: string,
  options: { enabled?: boolean } = {},
) {
  const isStreamConnected = useNotificationStreamStore(
    (state) => state.status === 'connected',
  )

  return useQuery<NotificationResponse, Error>({
    queryKey: notificationsQueryKey(userId),
    queryFn: () => fetchNotifications(userId, { limit: 50 }),
    staleTime: 0,
    refetchInterval: isStreamConnected ? false : NOTIFICATION_LIST_POLL_MS,
    enabled: Boolean(userId) && (options.enabled ?? true),
  })
}
