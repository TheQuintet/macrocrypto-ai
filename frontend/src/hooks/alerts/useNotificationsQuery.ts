import { useQuery } from '@tanstack/react-query'
import {
  fetchNotifications,
  notificationsQueryKey,
} from '@/api/alerts/notifications'
import type { NotificationResponse } from '@/types/alerts/notifications'

export function useNotificationsQuery(
  userId: string,
  options: { enabled?: boolean } = {},
) {
  return useQuery<NotificationResponse, Error>({
    queryKey: notificationsQueryKey(userId),
    queryFn: () => fetchNotifications(userId, { limit: 50 }),
    staleTime: 0,
    enabled: Boolean(userId) && (options.enabled ?? true),
  })
}
