import { useNavigate } from 'react-router-dom'
import { NotificationTypeIcon } from '@/components/alerts/notifications/NotificationTypeIcon'
import { Badge } from '@/components/ui/badge'
import { showToast } from '@/components/alerts/shared/ToastNotification'
import { useMarkNotificationReadMutation } from '@/hooks/alerts/useMarkNotificationReadMutation'
import { formatNotificationCopy } from '@/lib/alerts/formatNotificationToast'
import { notificationActionPath } from '@/lib/alerts/notificationActionPath'
import { cn } from '@/lib/utils'
import type { InAppNotification } from '@/types/alerts/notifications'

type NotificationItemProps = {
  notification: InAppNotification
  userId: string
  onNavigate?: () => void
}

export function NotificationItem({
  notification,
  userId,
  onNavigate,
}: NotificationItemProps) {
  const navigate = useNavigate()
  const markAsRead = useMarkNotificationReadMutation(userId)
  const copy = formatNotificationCopy(notification)
  const payloadLines = copy.payload?.split('\n').filter(Boolean) ?? []

  const handleClick = () => {
    showToast.dismiss(notification.id)
    if (!notification.read) {
      markAsRead.mutate(notification)
    }
    onNavigate?.()
    navigate(notificationActionPath(notification))
  }

  return (
    <button
      type="button"
      className={cn(
        'flex w-full gap-3 rounded-lg p-3 text-left transition-colors hover:bg-muted/50',
        notification.read
          ? 'bg-transparent'
          : 'bg-primary/10 ring-1 ring-primary/20',
        notification.is_archived && 'opacity-50',
      )}
      aria-label={
        notification.read
          ? notification.title
          : `${notification.title} (unread)`
      }
      onClick={handleClick}
    >
      <NotificationTypeIcon type={notification.notification_type} />
      <div className="min-w-0 flex-1">
        <p
          className={cn(
            'text-sm',
            notification.read ? 'font-medium' : 'font-semibold',
          )}
        >
          {copy.title}
        </p>
        <p className="text-xs font-medium text-muted-foreground">{copy.typeLabel}</p>
        {payloadLines.map((line) => (
          <p
            key={line}
            className="mt-1 text-sm text-muted-foreground"
          >
            {line}
          </p>
        ))}
        {copy.message ? (
          <p className="mt-1 text-sm text-muted-foreground">{copy.message}</p>
        ) : null}
        {copy.timestamp ? (
          <p className="mt-1 text-xs text-muted-foreground">{copy.timestamp}</p>
        ) : null}
      </div>
      {!notification.read ? <Badge className="mt-1">Unread</Badge> : null}
    </button>
  )
}
