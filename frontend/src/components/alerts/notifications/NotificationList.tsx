// src/components/alerts/notifications/NotificationList.tsx

import React, { useEffect } from 'react';
import { useNotificationStore } from '@/stores/alerts/notificationStore';
import { NotificationItem } from './NotificationItem';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { BellOff } from 'lucide-react';

interface NotificationListProps {
  userId: string;
}

export const NotificationList: React.FC<NotificationListProps> = ({ userId }) => {
  const {
    notifications,
    isLoading,
    error,
    fetchNotifications,
    markAllAsRead,
    unreadCount,
  } = useNotificationStore();

  useEffect(() => {
    if (userId) {
      fetchNotifications(userId);
    }
  }, [userId, fetchNotifications]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex gap-3">
            <Skeleton className="h-10 w-10 rounded-full" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-8 text-center text-muted-foreground">
        <p>Failed to load notifications</p>
        <Button
          variant="link"
          className="mt-2"
          onClick={() => fetchNotifications(userId)}
        >
          Retry
        </Button>
      </div>
    );
  }

  if (notifications.length === 0) {
    return (
      <div className="py-12 text-center">
        <BellOff className="h-12 w-12 mx-auto text-muted-foreground" />
        <p className="mt-4 text-muted-foreground">No notifications</p>
        <p className="text-sm text-muted-foreground">
          You're all caught up!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {unreadCount > 0 && (
        <div className="flex justify-end">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => markAllAsRead(userId)}
            className="text-xs"
          >
            Mark all as read
          </Button>
        </div>
      )}
      <div className="space-y-2">
        {notifications.map((notification) => (
          <NotificationItem
            key={notification.id}
            notification={notification}
          />
        ))}
      </div>
    </div>
  );
};
