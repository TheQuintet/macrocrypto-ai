import { BellOff } from 'lucide-react'
import { NotificationItem } from '@/components/alerts/notifications/NotificationItem'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useMarkAllNotificationsReadMutation } from '@/hooks/alerts/useMarkAllNotificationsReadMutation'
import { useNotificationsQuery } from '@/hooks/alerts/useNotificationsQuery'
import { useUnreadNotificationCountQuery } from '@/hooks/alerts/useUnreadNotificationCountQuery'
import { sortNotificationsByDateNewestFirst } from '@/lib/alerts/sortNotifications'

type NotificationListProps = {
  userId: string
  onNavigate?: () => void
}

export function NotificationList({ userId, onNavigate }: NotificationListProps) {
  const { data, isPending, isError, refetch } = useNotificationsQuery(userId)
  const { data: unread } = useUnreadNotificationCountQuery(userId)
  const markAllAsRead = useMarkAllNotificationsReadMutation(userId)

  const notifications = sortNotificationsByDateNewestFirst(
    data?.notifications ?? [],
  )
  const unreadCount = unread?.count ?? 0

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
    )
  }

  if (isError) {
    return (
      <div className="py-8 text-center text-muted-foreground">
        <p>Failed to load notifications</p>
        <Button
          variant="link"
          className="mt-2"
          onClick={() => {
            void refetch()
          }}
        >
          Retry
        </Button>
      </div>
    )
  }

  if (notifications.length === 0) {
    return (
      <div className="py-12 text-center">
        <BellOff className="mx-auto h-12 w-12 text-muted-foreground" />
        <p className="mt-4 text-muted-foreground">No notifications</p>
        <p className="text-sm text-muted-foreground">
          Fired alerts will show up here.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {unreadCount > 0 ? (
        <div className="flex justify-end">
          <Button
            variant="ghost"
            size="sm"
            className="text-xs"
            onClick={() => markAllAsRead.mutate()}
          >
            Mark all as read
          </Button>
        </div>
      ) : null}
      <div className="space-y-2" role="list">
        {notifications.map((notification) => (
          <div key={notification.id} role="listitem">
            <NotificationItem
              notification={notification}
              userId={userId}
              onNavigate={onNavigate}
            />
          </div>
        ))}
      </div>
    </div>
  )
}

export default NotificationList
