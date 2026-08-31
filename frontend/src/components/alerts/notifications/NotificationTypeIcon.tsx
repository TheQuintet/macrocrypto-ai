import { AlertCircle, Bell, Calendar, TrendingUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { NotificationType } from '@/types/alerts/notifications'

type NotificationTypeIconProps = {
  type: NotificationType
}

function iconForType(type: NotificationType) {
  switch (type) {
    case 'price_alert':
      return <Bell className="h-4 w-4" />
    case 'prediction_alert':
    case 'confidence_alert':
      return <TrendingUp className="h-4 w-4" />
    case 'macro_alert':
      return <Calendar className="h-4 w-4" />
    default:
      return <AlertCircle className="h-4 w-4" />
  }
}

function colorForType(type: NotificationType) {
  switch (type) {
    case 'price_alert':
      return 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400'
    case 'prediction_alert':
    case 'confidence_alert':
      return 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400'
    case 'macro_alert':
      return 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400'
    default:
      return 'bg-gray-100 text-gray-600 dark:bg-gray-800/50 dark:text-gray-400'
  }
}

export function NotificationTypeIcon({ type }: NotificationTypeIconProps) {
  return (
    <div
      className={cn(
        'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
        colorForType(type),
      )}
    >
      {iconForType(type)}
    </div>
  )
}
