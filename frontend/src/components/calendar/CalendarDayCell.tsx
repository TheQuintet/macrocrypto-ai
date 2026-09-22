import { useState } from 'react'
import { CalendarEventChip } from '@/components/calendar/CalendarEventChip'
import { formatDayHeading } from '@/lib/economicCalendarGrid'
import { cn } from '@/lib/utils'
import type { CalendarDay, EconomicEvent } from '@/types/economicCalendar'

const MAX_VISIBLE_EVENTS = 3

type CalendarDayCellProps = {
  day: CalendarDay
  timeZone: string
  isSubscribed: (event: EconomicEvent) => boolean | null
  onSelectEvent: (event: EconomicEvent) => void
}

export function CalendarDayCell({
  day,
  timeZone,
  isSubscribed,
  onSelectEvent,
}: CalendarDayCellProps) {
  const [expanded, setExpanded] = useState(false)
  const hiddenCount = day.events.length - MAX_VISIBLE_EVENTS
  const visibleEvents =
    expanded || hiddenCount <= 0
      ? day.events
      : day.events.slice(0, MAX_VISIBLE_EVENTS)

  return (
    <div
      role="gridcell"
      aria-label={formatDayHeading(day.key)}
      className={cn(
        'flex min-h-28 min-w-0 flex-col gap-1 border-r border-border p-1.5 last:border-r-0 lg:min-h-32',
        day.isToday
          ? 'bg-primary/10'
          : day.isCurrentPeriod
            ? 'bg-card'
            : 'bg-muted/40 text-muted-foreground/70',
      )}
    >
      <span
        className={cn(
          'ml-auto inline-flex size-7 shrink-0 items-center justify-center rounded-full text-xs',
          day.isToday
            ? 'bg-primary font-semibold text-primary-foreground'
            : day.isCurrentPeriod
              ? 'font-medium text-foreground'
              : 'text-muted-foreground/50',
        )}
      >
        {day.dayOfMonth}
        {day.isToday ? <span className="sr-only"> (today)</span> : null}
      </span>

      {visibleEvents.length > 0 ? (
        <div className="flex min-w-0 flex-col gap-0.5">
          {visibleEvents.map((event) => (
            <CalendarEventChip
              key={event.id}
              event={event}
              subscribed={isSubscribed(event)}
              timeZone={timeZone}
              onSelect={onSelectEvent}
            />
          ))}
          {!expanded && hiddenCount > 0 ? (
            <button
              type="button"
              className="px-1 py-0.5 text-left text-[11px] font-medium text-muted-foreground hover:text-foreground"
              onClick={() => setExpanded(true)}
            >
              +{hiddenCount} more
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
