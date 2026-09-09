import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bell } from 'lucide-react'
import { NotificationList } from './NotificationList'  // Make sure this import is correct
import { showToast } from '@/components/alerts/shared/ToastNotification'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { routes } from '@/constants/navigation'
import { useNotificationStream } from '@/hooks/alerts/useNotificationStream'
import { useNotificationsQuery } from '@/hooks/alerts/useNotificationsQuery'
import { useToastUnreadNotifications } from '@/hooks/alerts/useToastUnreadNotifications'
import { useUnreadNotificationCountQuery } from '@/hooks/alerts/useUnreadNotificationCountQuery'
import { formatUnreadBadgeCount } from '@/lib/alerts/formatUnreadBadgeCount'
import { cn } from '@/lib/utils'
import { useNotificationStreamStore } from '@/stores/notificationStreamStore'

type NotificationBellProps = {
  userId: string
  className?: string
}

export function NotificationBell({ userId, className }: NotificationBellProps) {
  const [isOpen, setIsOpen] = useState(false)
  const { data, isSuccess } = useUnreadNotificationCountQuery(userId)
  useNotificationsQuery(userId)
  useToastUnreadNotifications(userId)
  const unreadCount = data?.count ?? 0
  const unreadLabel = formatUnreadBadgeCount(unreadCount)
  const isStreamConnected = useNotificationStreamStore(
    (state) => state.status === 'connected',
  )
  const previousUnread = useRef<number | null>(null)

  useNotificationStream(userId)

  useEffect(() => {
    if (!isSuccess || data === undefined) return

    if (previousUnread.current === null) {
      previousUnread.current = data.count
      return
    }

    if (!isStreamConnected && data.count > previousUnread.current) {
      showToast.info(
        'New alert',
        'Open notifications to see the latest alert.',
      )
    }
    previousUnread.current = data.count
  }, [data, isStreamConnected, isSuccess])

  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <Tooltip>
        <TooltipTrigger asChild>
          <SheetTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={cn('relative', className)}
              aria-label="Notifications"
            >
              <Bell
                className={cn(
                  unreadCount > 0 && 'text-green-600 dark:text-green-500',
                )}
              />
              {unreadLabel ? (
                <Badge
                  className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center border-transparent bg-green-600 p-0 text-xs text-white dark:bg-green-500 dark:text-green-950"
                >
                  {unreadLabel}
                </Badge>
              ) : null}
            </Button>
          </SheetTrigger>
        </TooltipTrigger>
        <TooltipContent>Notifications</TooltipContent>
      </Tooltip>
      <SheetContent side="right" className="flex w-full flex-col sm:max-w-lg">
        <SheetHeader className="pr-12">
          <SheetTitle className="flex w-fit max-w-full items-center gap-2">
            <span>Notifications</span>
            {unreadCount > 0 ? (
              <span className="text-sm font-normal text-muted-foreground">
                {unreadCount} unread
              </span>
            ) : null}
          </SheetTitle>
        </SheetHeader>
        <div className="min-h-0 flex-1 overflow-y-auto px-4">
          <NotificationList
            userId={userId}
            onNavigate={() => setIsOpen(false)}
          />
        </div>
        <SheetFooter>
          <Button variant="outline" className="w-full" asChild>
            <Link to={routes.alerts} onClick={() => setIsOpen(false)}>
              Manage alerts
            </Link>
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
