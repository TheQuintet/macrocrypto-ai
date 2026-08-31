import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bell } from 'lucide-react'
import { NotificationList } from '@/components/alerts/notifications/NotificationList'
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
import { cn } from '@/lib/utils'
import { useNotificationStore } from '@/stores/alerts/notificationStore'

type NotificationBellProps = {
  userId: string
  className?: string
}

export function NotificationBell({ userId, className }: NotificationBellProps) {
  const [isOpen, setIsOpen] = useState(false)
  const { unreadCount, fetchNotifications, fetchUnreadCount } =
    useNotificationStore()

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (open) {
      fetchNotifications(userId)
    }
  }

  useEffect(() => {
    if (!userId) return

    fetchUnreadCount(userId)
    const interval = setInterval(() => {
      fetchUnreadCount(userId)
    }, 30_000)
    return () => clearInterval(interval)
  }, [userId, fetchUnreadCount])

  return (
    <Sheet open={isOpen} onOpenChange={handleOpenChange}>
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
              <Bell />
              {unreadCount > 0 ? (
                <Badge
                  variant="destructive"
                  className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center p-0 text-xs"
                >
                  {unreadCount > 99 ? '99+' : unreadCount}
                </Badge>
              ) : null}
            </Button>
          </SheetTrigger>
        </TooltipTrigger>
        <TooltipContent>Notifications</TooltipContent>
      </Tooltip>
      <SheetContent side="right" className="flex w-full flex-col sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="flex items-center justify-between gap-2">
            <span>Notifications</span>
            {unreadCount > 0 ? (
              <span className="text-sm font-normal text-muted-foreground">
                {unreadCount} unread
              </span>
            ) : null}
          </SheetTitle>
        </SheetHeader>
        <div className="min-h-0 flex-1 overflow-y-auto px-4">
          <NotificationList userId={userId} />
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
