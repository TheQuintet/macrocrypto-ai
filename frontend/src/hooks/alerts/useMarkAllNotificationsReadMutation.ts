import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  markAllNotificationsAsRead,
  notificationsQueryKey,
  unreadNotificationCountQueryKey,
} from '@/api/alerts/notifications'
import { showToast } from '@/components/alerts/shared/ToastNotification'
import type { NotificationResponse } from '@/types/alerts/notifications'

export function useMarkAllNotificationsReadMutation(userId: string) {
  const queryClient = useQueryClient()

  return useMutation<{ count: number }, Error, void>({
    mutationFn: () => markAllNotificationsAsRead(userId),
    onSuccess: () => {
      const now = new Date().toISOString()
      queryClient.setQueryData<NotificationResponse>(
        notificationsQueryKey(userId),
        (current) => {
          if (!current) return current
          return {
            ...current,
            notifications: current.notifications.map((item) => ({
              ...item,
              read: true,
              read_at: item.read_at ?? now,
            })),
          }
        },
      )
      queryClient.setQueryData<{ count: number }>(
        unreadNotificationCountQueryKey(userId),
        { count: 0 },
      )
      showToast.dismissAll()
    },
  })
}
