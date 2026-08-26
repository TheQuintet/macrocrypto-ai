// src/components/alerts/notifications/NotificationItem.tsx

import React from 'react';
import type { InAppNotification } from '@/types/alerts/priceAlert';
import { useNotificationStore } from '@/stores/alerts/notificationStore';
import { cn } from '@/lib/utils';
import { Bell, TrendingUp, Calendar, AlertCircle } from 'lucide-react';

interface NotificationItemProps {
  notification: InAppNotification;
}

const getIcon = (type: string) => {
  switch (type) {
    case 'price_alert':
      return <Bell className="h-4 w-4" />;
    case 'prediction_alert':
      return <TrendingUp className="h-4 w-4" />;
    case 'macro_alert':
      return <Calendar className="h-4 w-4" />;
    default:
      return <AlertCircle className="h-4 w-4" />;
  }
};

const getColor = (type: string) => {
  switch (type) {
    case 'price_alert':
      return 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400';
    case 'prediction_alert':
      return 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400';
    case 'macro_alert':
      return 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400';
    default:
      return 'bg-gray-100 text-gray-600 dark:bg-gray-800/50 dark:text-gray-400';
  }
};

export const NotificationItem: React.FC<NotificationItemProps> = ({
  notification,
}) => {
  const { markAsRead } = useNotificationStore();

  const handleClick = () => {
    if (!notification.read) {
      markAsRead(notification.id);
    }
    // Navigate to action_url if present
    if (notification.action_url) {
      window.location.href = notification.action_url;
    }
  };

  return (
    <div
      className={cn(
        'flex gap-3 p-3 rounded-lg cursor-pointer transition-colors hover:bg-muted/50',
        !notification.read ? 'bg-muted/30' : '',
        notification.is_archived && 'opacity-50'
      )}
      onClick={handleClick}
    >
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          getColor(notification.notification_type)
        )}
      >
        {getIcon(notification.notification_type)}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{notification.title}</p>
        <p className="text-sm text-muted-foreground line-clamp-2">
          {notification.message}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          {new Date(notification.created_at).toLocaleString()}
        </p>
      </div>
      {!notification.read && (
        <span className="h-2 w-2 shrink-0 mt-2 rounded-full bg-blue-500" />
      )}
    </div>
  );
};
