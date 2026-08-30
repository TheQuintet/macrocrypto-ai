import { useId } from 'react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import type { AlertStatus } from '@/types/alerts/priceAlert'
import { getAlertStatusBadgeConfig } from './alertStatusBadgeConfig'
import { isAlertEnabled, resolveAlertStatus } from './alertStatus'

type AlertStatusToggleProps = {
  status: AlertStatus | string
  onToggle: () => void
  size?: 'sm' | 'default'
}

export function AlertStatusToggle({
  status,
  onToggle,
  size = 'sm',
}: AlertStatusToggleProps) {
  const switchId = useId()
  const resolved = resolveAlertStatus(status)
  const enabled = resolved ? isAlertEnabled(resolved) : false
  const config = getAlertStatusBadgeConfig(status)

  return (
    <Badge
      asChild
      variant="secondary"
      className={cn(
        'cursor-pointer font-medium hover:opacity-90',
        config.className,
        size === 'sm' ? 'h-auto gap-1 py-0.5 pr-2 pl-0.5 text-xs' : 'h-auto gap-1.5 py-0.5 pr-2.5 pl-1 text-sm',
      )}
    >
      <label htmlFor={switchId}>
        <Switch
          id={switchId}
          size="sm"
          checked={enabled}
          onCheckedChange={() => onToggle()}
          aria-label={enabled ? 'Deactivate alert' : 'Activate alert'}
        />
        {config.label}
      </label>
    </Badge>
  )
}
