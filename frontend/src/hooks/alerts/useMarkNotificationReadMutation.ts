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

  return useMutation<InAppNotification, Error, string>({
    mutationFn: (notificationId) => markNotificationAsRead(notificationId),
    onSuccess: (updated) => {
      queryClient.setQueryData<NotificationResponse>(
        notificationsQueryKey(userId),
        (current) => {
          if (!current) return current
          return {
            ...current,
            notifications: current.notifications.map((item) =>
              item.id === updated.id ? updated : item,
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
