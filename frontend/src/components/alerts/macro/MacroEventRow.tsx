import { Calendar } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { AlertRepeatBadge } from '@/components/alerts/shared/AlertRepeatBadge'
import { AlertRowDeleteButton } from '@/components/alerts/shared/AlertRowDeleteButton'
import { AlertStatusToggle } from '@/components/alerts/shared/AlertStatusToggle'
import { AlertTableNameCell } from '@/components/alerts/shared/AlertTableNameCell'
import { AlertTableRow } from '@/components/alerts/shared/AlertTableRow'
import { cn } from '@/lib/utils'
import type { EventImpact, MacroSubscription } from '@/types/alerts/macroAlert'
import {
  MACRO_EVENT_TITLES,
  MACRO_TIMING_LABELS,
} from './macroEventCopy'

const impactBadgeColors: Record<EventImpact, string> = {
  HIGH: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  MEDIUM: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  LOW: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
}

/** Shown wherever the alert service has no value to report. */
function NotProvided() {
  return <span className="text-xs text-muted-foreground">—</span>
}

type MacroEventRowProps = {
  subscription: MacroSubscription
  onSubscribeChange: (subscriptionId: string, subscribed: boolean) => void
  onDelete: (subscriptionId: string) => void
  onEdit: (subscription: MacroSubscription) => void
}

export function MacroEventRow({
  subscription,
  onSubscribeChange,
  onDelete,
  onEdit,
}: MacroEventRowProps) {
  const isActive = subscription.subscribed
  const { impact_filter: impact, timing, one_time: oneTime } = subscription

  return (
    <AlertTableRow
      onOpen={() => onEdit(subscription)}
      name={
        <AlertTableNameCell
          icon={Calendar}
          name={MACRO_EVENT_TITLES[subscription.event_type]}
          onOpen={() => onEdit(subscription)}
          openLabel="Edit alert"
          badge={
            impact ? (
              <Badge
                variant="outline"
                className={cn('shrink-0 text-xs', impactBadgeColors[impact])}
              >
                {impact}
              </Badge>
            ) : null
          }
        />
      }
      detail={
        timing ? (
          <p className="text-sm">Alerts {MACRO_TIMING_LABELS[timing]}</p>
        ) : (
          <NotProvided />
        )
      }
      repeat={oneTime === null ? <NotProvided /> : <AlertRepeatBadge oneTime={oneTime} />}
      status={
        <AlertStatusToggle
          status={isActive ? 'active' : 'disabled'}
          onToggle={() => onSubscribeChange(subscription.id, !isActive)}
        />
      }
      actions={
        <AlertRowDeleteButton
          onClick={() => onDelete(subscription.id)}
          disabled={!isActive}
          title={isActive ? 'Delete alert' : 'No alert set for this event'}
        />
      }
    />
  )
}
