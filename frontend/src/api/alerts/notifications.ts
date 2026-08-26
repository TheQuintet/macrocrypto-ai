// src/api/alerts/notifications.ts

import apiClient from '@/lib/apiClient';
import type { InAppNotification, NotificationResponse } from '@/types/alerts/priceAlert';

export const notificationApi = {
  // Get all notifications
  getNotifications: async (
    userId: string,
    params?: { unread_only?: boolean; limit?: number; offset?: number }
  ): Promise<NotificationResponse> => {
    const response = await apiClient.get('/notifications', {
      params: { user_id: userId, ...params },
    });
    return response.data;
  },

  // Get unread count
  getUnreadCount: async (userId: string): Promise<{ count: number }> => {
    const response = await apiClient.get('/notifications/unread', {
      params: { user_id: userId },
    });
    return response.data;
  },

  // Mark notification as read
  markAsRead: async (notificationId: string): Promise<InAppNotification> => {
    const response = await apiClient.put(`/notifications/${notificationId}/read`);
    return response.data;
  },

  // Mark all as read
  markAllAsRead: async (userId: string): Promise<{ count: number }> => {
    const response = await apiClient.post('/notifications/read-all', { user_id: userId });
    return response.data;
  },
};
