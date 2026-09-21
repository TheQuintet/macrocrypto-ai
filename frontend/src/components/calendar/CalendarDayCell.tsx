import { CalendarEventChip } from '@/components/calendar/CalendarEventChip'
import { formatDayHeading } from '@/lib/economicCalendarGrid'
import { cn } from '@/lib/utils'
import type { CalendarDay, EconomicEvent } from '@/types/economicCalendar'

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
  return (
    <div
      role="gridcell"
      aria-label={formatDayHeading(day.key)}
      className={cn(
        'flex min-h-24 min-w-0 flex-col gap-1 border-t border-l border-border p-1.5',
        day.isCurrentPeriod ? 'bg-card' : 'bg-muted/40',
      )}
    >
      <span
        className={cn(
          'inline-flex size-6 shrink-0 items-center justify-center rounded-full text-xs',
          day.isCurrentPeriod
            ? 'text-foreground'
            : 'text-muted-foreground/60',
          day.isToday && 'bg-primary font-semibold text-primary-foreground',
        )}
      >
        {day.dayOfMonth}
        {day.isToday ? <span className="sr-only"> (today)</span> : null}
      </span>

      {day.events.length > 0 ? (
        <div className="flex min-w-0 flex-col gap-0.5 overflow-y-auto">
          {day.events.map((event) => (
            <CalendarEventChip
              key={event.id}
              event={event}
              subscribed={isSubscribed(event)}
              timeZone={timeZone}
              onSelect={onSelectEvent}
            />
          ))}
        </div>
      ) : null}
    </div>
  )
}
