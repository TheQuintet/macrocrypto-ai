import { Bell } from 'lucide-react'
import { getEventImpactBadgeConfig } from '@/components/calendar/eventImpactBadgeConfig'
import { formatEventTime } from '@/lib/economicCalendarGrid'
import { cn } from '@/lib/utils'
import type { EconomicEvent } from '@/types/economicCalendar'

type CalendarEventChipProps = {
  event: EconomicEvent
  /** `null` when the subscription lookup failed — unknown, not unsubscribed. */
  subscribed: boolean | null
  timeZone: string
  onSelect: (event: EconomicEvent) => void
  className?: string
}

function subscriptionLabel(subscribed: boolean | null): string {
  if (subscribed === null) {
    return 'alert status unavailable'
  }

  return subscribed ? 'alerts on' : 'no alerts'
}

/**
 * One event inside a day cell. The impact dot and bell carry meaning that
 * colour alone would not, so both are spelled out in the accessible name.
 */
export function CalendarEventChip({
  event,
  subscribed,
  timeZone,
  onSelect,
  className,
}: CalendarEventChipProps) {
  const impact = getEventImpactBadgeConfig(event.impact_level)
  const time = formatEventTime(event.event_date, timeZone)

  return (
    <button
      type="button"
      onClick={() => onSelect(event)}
      aria-label={`${event.event_name}, ${time}, ${impact.label}, ${subscriptionLabel(subscribed)}`}
      className={cn(
        'flex w-full min-w-0 items-center gap-1.5 rounded-md px-1.5 py-1 text-left text-xs',
        'touch-manipulation hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        className,
      )}
    >
      <span
        aria-hidden
        className={cn('size-1.5 shrink-0 rounded-full', impact.dot)}
      />
      <span className="shrink-0 tabular-nums text-muted-foreground">
        {time}
      </span>
      <span className="truncate">{event.event_name}</span>
      {subscribed === true ? (
        <Bell
          aria-hidden
          className="ml-auto size-3 shrink-0 text-green-600 dark:text-green-400"
        />
      ) : null}
    </button>
  )
}
