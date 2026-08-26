// src/stores/alerts/notificationStore.ts

import { create } from 'zustand';
import type { InAppNotification } from '@/types/alerts/priceAlert';
import { notificationApi } from '@/api/alerts/notifications';

interface NotificationState {
  notifications: InAppNotification[];
  unreadCount: number;
  isLoading: boolean;
  error: string | null;
  fetchNotifications: (userId: string, params?: { unread_only?: boolean }) => Promise<void>;
  fetchUnreadCount: (userId: string) => Promise<void>;
  markAsRead: (notificationId: string) => Promise<void>;
  markAllAsRead: (userId: string) => Promise<void>;
  clearError: () => void;
}

// Helper to extract error message
const getErrorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  unreadCount: 0,
  isLoading: false,
  error: null,

  fetchNotifications: async (userId, params) => {
    set({ isLoading: true, error: null });
    try {
      const response = await notificationApi.getNotifications(userId, { ...params, limit: 50 });
      set({ notifications: response.notifications || [], isLoading: false });
    } catch (error) {
      set({ error: getErrorMessage(error), isLoading: false });
    }
  },

  fetchUnreadCount: async (userId) => {
    try {
      const response = await notificationApi.getUnreadCount(userId);
      set({ unreadCount: response.count });
    } catch (error) {
      // Silently fail for unread count
      console.error('Failed to fetch unread count:', error);
    }
  },

  markAsRead: async (notificationId) => {
    try {
      await notificationApi.markAsRead(notificationId);
      set((state) => ({
        notifications: state.notifications.map((n) =>
          n.id === notificationId ? { ...n, read: true, read_at: new Date().toISOString() } : n
        ),
        unreadCount: Math.max(0, state.unreadCount - 1),
      }));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
      throw error;
    }
  },

  markAllAsRead: async (userId) => {
    try {
      await notificationApi.markAllAsRead(userId);
      set((state) => ({
        notifications: state.notifications.map((n) => ({
          ...n,
          read: true,
          read_at: new Date().toISOString(),
        })),
        unreadCount: 0,
      }));
    } catch (error) {
      console.error('Failed to mark all as read:', error);
      throw error;
    }
  },

  clearError: () => set({ error: null }),
}));
