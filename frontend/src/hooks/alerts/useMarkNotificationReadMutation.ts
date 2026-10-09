import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  markNotificationAsRead,
  notificationsQueryKey,
  unreadNotificationCountQueryKey,
} from '@/api/alerts/notifications'
import type {
  InAppNotification,
  NotificationResponse,
} from '@/types/alerts/notifications'

export function useMarkNotificationReadMutation(userId: string) {
  const queryClient = useQueryClient()

  return useMutation<void, Error, Pick<InAppNotification, 'id' | 'source' | 'notification_type'>>({
    mutationFn: (notification) => markNotificationAsRead(notification),
    onSuccess: (_result, { id: notificationId }) => {
      const readAt = new Date().toISOString()
      queryClient.setQueryData<NotificationResponse>(
        notificationsQueryKey(userId),
        (current) => {
          if (!current) return current
          return {
            ...current,
            notifications: current.notifications.map((item) =>
              item.id === notificationId
                ? { ...item, read: true, read_at: item.read_at ?? readAt }
                : item,
            ),
          }
        },
      )
      queryClient.setQueryData<{ count: number }>(
        unreadNotificationCountQueryKey(userId),
        (current) => ({ count: Math.max(0, (current?.count ?? 1) - 1) }),
      )
    },
  })
}
