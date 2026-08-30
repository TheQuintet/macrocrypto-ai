import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import type { AlertStatus } from '@/types/alerts/priceAlert'
import { getAlertStatusBadgeConfig } from './alertStatusBadgeConfig'

interface AlertStatusBadgeProps {
  status: AlertStatus | string
  className?: string
  size?: 'sm' | 'default'
}

export function AlertStatusBadge({
  status,
  className,
  size = 'default',
}: AlertStatusBadgeProps) {
  const config = getAlertStatusBadgeConfig(status)

  return (
    <Badge
      variant="secondary"
      className={cn(
        'inline-flex items-center gap-1.5 font-medium',
        config.className,
        size === 'sm' ? 'px-2 py-0 text-xs' : 'px-2.5 py-0.5 text-sm',
        className,
      )}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full', config.dot)} />
      {config.label}
    </Badge>
  )
}
