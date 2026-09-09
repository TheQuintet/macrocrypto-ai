import { useNotificationsQuery } from '@/hooks/alerts/useNotificationsQuery';
import { useUnreadNotificationCountQuery } from '@/hooks/alerts/useUnreadNotificationCountQuery';
import { useMarkAllNotificationsReadMutation } from '@/hooks/alerts/useMarkAllNotificationsReadMutation';
import { NotificationItem } from './NotificationItem';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { BellOff } from 'lucide-react';
import { showToast } from '@/components/alerts/shared/ToastNotification';
import { sortNotificationsByDateNewestFirst } from '@/lib/alerts/sortNotifications';

interface NotificationListProps {
  userId: string;
  onNavigate?: () => void;
}

export function NotificationList({ userId, onNavigate }: NotificationListProps) {
  const { data, isPending, isError, refetch } = useNotificationsQuery(userId);
  const { data: unreadData } = useUnreadNotificationCountQuery(userId);
  const markAllAsRead = useMarkAllNotificationsReadMutation(userId);

  const notifications = sortNotificationsByDateNewestFirst(
    data?.notifications ?? []
  );
  const unreadCount = unreadData?.count ?? 0;

  const handleMarkAllAsRead = async () => {
    try {
      await markAllAsRead.mutateAsync();
      showToast.success('All notifications marked as read');
    } catch {
      showToast.error('Failed to mark all as read');
    }
  };

  if (isPending) {
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

  if (isError) {
    return (
      <div className="py-8 text-center text-muted-foreground">
        <p>Failed to load notifications</p>
        <Button
          variant="link"
          className="mt-2"
          onClick={() => refetch()}
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
            onClick={handleMarkAllAsRead}
            className="text-xs"
            disabled={markAllAsRead.isPending}
          >
            {markAllAsRead.isPending ? 'Marking...' : `Mark all as read (${unreadCount})`}
          </Button>
        </div>
      )}
      <div className="space-y-2">
        {notifications.map((notification) => (
          <NotificationItem
            key={notification.id}
            notification={notification}
            onNavigate={onNavigate}
          />
        ))}
      </div>
    </div>
  );
}

export default NotificationList;
