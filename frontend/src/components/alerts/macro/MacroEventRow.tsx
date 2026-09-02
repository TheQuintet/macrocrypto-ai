import { Calendar, Clock } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { AlertRepeatBadge } from '@/components/alerts/shared/AlertRepeatBadge'
import { AlertRowDeleteButton } from '@/components/alerts/shared/AlertRowDeleteButton'
import { AlertStatusToggle } from '@/components/alerts/shared/AlertStatusToggle'
import { AlertTableNameCell } from '@/components/alerts/shared/AlertTableNameCell'
import { AlertTableRow } from '@/components/alerts/shared/AlertTableRow'
import { cn } from '@/lib/utils'
import type { MacroEventSubscription } from '@/hooks/alerts/useMacroEvents'
import type { EventImpact, MacroEvent } from '@/types/alerts/macroAlert'
import { MACRO_TIMING_LABELS } from './macroEventCopy'

const impactBadgeColors: Record<EventImpact, string> = {
  HIGH: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  MEDIUM: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  LOW: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
}

function formatTimeLeft(scheduledAt: string) {
  const diffHours = Math.round((new Date(scheduledAt).getTime() - Date.now()) / (1000 * 60 * 60))
  const diffDays = Math.floor(diffHours / 24)

  if (diffDays > 0) return `${diffDays}d ${diffHours % 24}h left`
  if (diffHours > 0) return `${diffHours}h left`
  return 'Now'
}

type MacroEventRowProps = {
  event: MacroEvent
  subscription?: MacroEventSubscription
  onSubscribeChange: (eventId: string, subscribed: boolean) => void
  onDelete: (eventId: string) => void
  onEdit: (event: MacroEvent) => void
}

export function MacroEventRow({
  event,
  subscription,
  onSubscribeChange,
  onDelete,
  onEdit,
}: MacroEventRowProps) {
  const isActive = event.subscribed
  const timing = isActive ? subscription?.timing : undefined
  const scheduledAt = new Date(event.scheduled_at).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
  const timeLeft = formatTimeLeft(event.scheduled_at)

  return (
    <AlertTableRow onOpen={() => onEdit(event)}>
      <td className="px-4 py-3">
        <AlertTableNameCell
          icon={Calendar}
          name={event.event_name}
          secondary={event.description}
          onOpen={() => onEdit(event)}
          openLabel="Edit alert"
          badge={
            <Badge
              variant="outline"
              className={cn('shrink-0 text-xs', impactBadgeColors[event.impact])}
            >
              {event.impact}
            </Badge>
          }
        />
      </td>
      <td className="px-4 py-3">
        <p className="text-sm">{scheduledAt}</p>
        <div className="mt-0.5 flex flex-wrap items-center gap-1.5">
          <span className="text-xs text-muted-foreground">{timeLeft}</span>
          {timing ? (
            <Badge variant="secondary" className="gap-1 text-xs">
              <Clock className="h-3 w-3" />
              Alerts {MACRO_TIMING_LABELS[timing]}
            </Badge>
          ) : null}
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="flex justify-center">
          {isActive ? (
            <AlertRepeatBadge oneTime={subscription?.oneTime ?? true} />
          ) : (
            <span className="text-xs text-muted-foreground">—</span>
          )}
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="flex justify-center">
          <AlertStatusToggle
            status={isActive ? 'active' : 'disabled'}
            onToggle={() => onSubscribeChange(event.id, !isActive)}
          />
        </div>
      </td>
      <td className="px-4 py-3 text-right">
        <AlertRowDeleteButton
          onClick={() => onDelete(event.id)}
          disabled={!isActive}
          title={isActive ? 'Delete alert' : 'No alert set for this event'}
        />
      </td>
    </AlertTableRow>
  )
}
