import { NotificationItem } from '@/components/alerts/notifications/NotificationItem'
import type { InAppNotification } from '@/types/alerts/notifications'

type NotificationListGroupProps = {
  heading: string
  notifications: InAppNotification[]
  userId: string
  onNavigate?: () => void
}

export function NotificationListGroup({
  heading,
  notifications,
  userId,
  onNavigate,
}: NotificationListGroupProps) {
  if (notifications.length === 0) {
    return null
  }

  return (
    <section className="space-y-2">
      <h3 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
        {heading}
      </h3>
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
    </section>
  )
}
