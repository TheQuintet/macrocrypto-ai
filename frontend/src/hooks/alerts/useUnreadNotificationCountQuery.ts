import { useQuery } from '@tanstack/react-query'
import {
  fetchUnreadNotificationCount,
  unreadNotificationCountQueryKey,
} from '@/api/alerts/notifications'
import { useNotificationStreamStore } from '@/stores/notificationStreamStore'

/** Unread badge poll — stands down while the live stream is connected. */
export const UNREAD_NOTIFICATION_POLL_MS = 30_000

export function useUnreadNotificationCountQuery(userId: string) {
  const isStreamConnected = useNotificationStreamStore(
    (state) => state.status === 'connected',
  )

  return useQuery<{ count: number }, Error>({
    queryKey: unreadNotificationCountQueryKey(userId),
    queryFn: () => fetchUnreadNotificationCount(userId),
    refetchInterval: isStreamConnected ? false : UNREAD_NOTIFICATION_POLL_MS,
    enabled: Boolean(userId),
  })
}
