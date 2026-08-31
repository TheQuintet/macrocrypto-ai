import apiClient from '@/lib/apiClient'
import {
  simulateGetNotifications,
  simulateGetUnreadCount,
  simulateMarkAllAsRead,
  simulateMarkAsRead,
} from './simulatedNotifications'
import { withSimulatedFallback } from './withSimulatedFallback'
import type { InAppNotification, NotificationResponse } from '@/types/alerts/priceAlert'

export const notificationApi = {
  getNotifications: async (
    userId: string,
    params?: { unread_only?: boolean; limit?: number; offset?: number },
  ): Promise<NotificationResponse> =>
    withSimulatedFallback(
      async () => {
        const response = await apiClient.get('/notifications', {
          params: { user_id: userId, ...params },
        })
        return response.data
      },
      () => simulateGetNotifications(userId, params),
    ),

  getUnreadCount: async (userId: string): Promise<{ count: number }> =>
    withSimulatedFallback(
      async () => {
        const response = await apiClient.get('/notifications/unread', {
          params: { user_id: userId },
        })
        return response.data
      },
      () => simulateGetUnreadCount(userId),
    ),

  markAsRead: async (notificationId: string): Promise<InAppNotification> =>
    withSimulatedFallback(
      async () => {
        const response = await apiClient.put(
          `/notifications/${notificationId}/read`,
        )
        return response.data
      },
      () => simulateMarkAsRead(notificationId),
    ),

  markAllAsRead: async (userId: string): Promise<{ count: number }> =>
    withSimulatedFallback(
      async () => {
        const response = await apiClient.post('/notifications/read-all', {
          user_id: userId,
        })
        return response.data
      },
      () => simulateMarkAllAsRead(userId),
    ),
}
