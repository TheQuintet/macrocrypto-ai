import { Bell, BellOff, HelpCircle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

type SubscriptionStatusBadgeProps = {
  /** `null` when the subscription lookup failed — unknown, not unsubscribed. */
  subscribed: boolean | null
  className?: string
}

const BADGE_STATES = {
  on: {
    Icon: Bell,
    label: 'Alerts on',
    className:
      'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  },
  off: {
    Icon: BellOff,
    label: 'No alerts',
    className: 'bg-muted text-muted-foreground',
  },
  unknown: {
    Icon: HelpCircle,
    label: 'Alert status unavailable',
    className: 'bg-muted text-muted-foreground',
  },
} as const

/**
 * Whether this event would alert the user. Read-only here — subscriptions are
 * managed on the alerts page (T9.7), not from the calendar.
 */
export function SubscriptionStatusBadge({
  subscribed,
  className,
}: SubscriptionStatusBadgeProps) {
  const state =
    subscribed === null
      ? BADGE_STATES.unknown
      : subscribed
        ? BADGE_STATES.on
        : BADGE_STATES.off

  return (
    <Badge
      variant="secondary"
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 text-sm font-medium',
        state.className,
        className,
      )}
    >
      <state.Icon aria-hidden className="size-3.5" />
      {state.label}
    </Badge>
  )
}
