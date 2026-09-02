import { CalendarEventChip } from '@/components/calendar/CalendarEventChip'
import { formatDayHeading } from '@/lib/economicCalendarGrid'
import { cn } from '@/lib/utils'
import type { CalendarGrid, EconomicEvent } from '@/types/economicCalendar'

type CalendarAgendaProps = {
  grid: CalendarGrid
  timeZone: string
  isSubscribed: (event: EconomicEvent) => boolean | null
  onSelectEvent: (event: EconomicEvent) => void
}

/**
 * The mobile face of the same period: only the days that actually have
 * releases, in order. Shown below `md`, where the grid is hidden.
 */
export function CalendarAgenda({
  grid,
  timeZone,
  isSubscribed,
  onSelectEvent,
}: CalendarAgendaProps) {
  const daysWithEvents = grid.days.filter(
    (day) => day.isCurrentPeriod && day.events.length > 0,
  )

  return (
    <div
      aria-label={`Economic calendar agenda, ${grid.label}`}
      className="flex min-w-0 flex-col gap-3 md:hidden"
    >
      {daysWithEvents.length === 0 ? (
        <p className="rounded-lg border border-border bg-card px-3 py-6 text-center text-sm text-muted-foreground">
          No events in {grid.label}.
        </p>
      ) : (
        daysWithEvents.map((day) => (
          <section
            key={day.key}
            className="min-w-0 rounded-lg border border-border bg-card"
          >
            <h3
              className={cn(
                'border-b border-border px-3 py-2 text-xs font-medium',
                day.isToday ? 'text-primary' : 'text-muted-foreground',
              )}
            >
              {formatDayHeading(day.key)}
              {day.isToday ? ' · Today' : ''}
            </h3>
            <div className="flex min-w-0 flex-col gap-1 p-1.5">
              {day.events.map((event) => (
                <CalendarEventChip
                  key={event.id}
                  event={event}
                  subscribed={isSubscribed(event)}
                  timeZone={timeZone}
                  onSelect={onSelectEvent}
                  className="min-h-9 text-sm"
                />
              ))}
            </div>
          </section>
        ))
      )}
    </div>
  )
}
