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
 * One event inside a day cell. The impact bullet is the only colour cue;
 * the time and name stay on the standard foreground so they stay readable.
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
        'flex w-full min-w-0 items-start gap-1 rounded px-1 py-0.5 text-left text-[11px] leading-4 text-foreground',
        'touch-manipulation hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        className,
      )}
    >
      <span
        aria-hidden
        className={cn('mt-1.5 size-1.5 shrink-0 rounded-full', impact.dot)}
      />
      <span className="min-w-0 whitespace-normal break-words">
        <span className="tabular-nums text-muted-foreground">{time} </span>
        <span>{event.event_name}</span>
      </span>
    </button>
  )
}
