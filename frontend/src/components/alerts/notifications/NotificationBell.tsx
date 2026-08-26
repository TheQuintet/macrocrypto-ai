// src/components/alerts/notifications/NotificationBell.tsx

import React, { useState, useEffect } from 'react';
import { Bell } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { NotificationList } from './NotificationList';
import { useNotificationStore } from '@/stores/alerts/notificationStore';
import { cn } from '@/lib/utils';

interface NotificationBellProps {
  userId: string;
  className?: string;
}

export const NotificationBell: React.FC<NotificationBellProps> = ({
  userId,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const { unreadCount, fetchNotifications, fetchUnreadCount } =
    useNotificationStore();

  // Fetch notifications when bell is clicked
  const handleOpenChange = (open: boolean) => {
    setIsOpen(open);
    if (open) {
      fetchNotifications(userId);
    }
  };

  // Fetch unread count periodically
  useEffect(() => {
    if (userId) {
      fetchUnreadCount(userId);
      // Refresh unread count every 30 seconds
      const interval = setInterval(() => {
        fetchUnreadCount(userId);
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [userId, fetchUnreadCount]);

  return (
    <Sheet open={isOpen} onOpenChange={handleOpenChange}>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className={cn('relative', className)}
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
            >
              {unreadCount > 99 ? '99+' : unreadCount}
            </Badge>
          )}
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="w-full sm:w-[400px]">
        <SheetHeader>
          <SheetTitle className="flex items-center justify-between">
            <span>Notifications</span>
            {unreadCount > 0 && (
              <span className="text-sm font-normal text-muted-foreground">
                {unreadCount} unread
              </span>
            )}
          </SheetTitle>
        </SheetHeader>
        <div className="mt-4 h-[calc(100vh-100px)] overflow-y-auto">
          <NotificationList userId={userId} />
        </div>
      </SheetContent>
    </Sheet>
  );
};
