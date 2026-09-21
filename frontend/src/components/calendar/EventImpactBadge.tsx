import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { getEventImpactBadgeConfig } from '@/components/calendar/eventImpactBadgeConfig'
import type { EventImpactLevel } from '@/types/economicCalendar'

type EventImpactBadgeProps = {
  impact: EventImpactLevel | string
  className?: string
  size?: 'sm' | 'default'
}

export function EventImpactBadge({
  impact,
  className,
  size = 'default',
}: EventImpactBadgeProps) {
  const config = getEventImpactBadgeConfig(impact)

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
      {size === 'sm' ? config.shortLabel : config.label}
    </Badge>
  )
}
