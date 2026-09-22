import { CalendarDayCell } from '@/components/calendar/CalendarDayCell'
import { weekdayLabels } from '@/lib/economicCalendarGrid'
import type { CalendarGrid as CalendarGridData, EconomicEvent } from '@/types/economicCalendar'

type CalendarGridProps = {
  grid: CalendarGridData
  timeZone: string
  isSubscribed: (event: EconomicEvent) => boolean | null
  onSelectEvent: (event: EconomicEvent) => void
}

/**
 * The seven-column month/week grid. Hidden on narrow screens, where
 * `CalendarAgenda` shows the same period as a scannable list instead —
 * seven columns of day cells do not survive a phone.
 */
export function CalendarGrid({
  grid,
  timeZone,
  isSubscribed,
  onSelectEvent,
}: CalendarGridProps) {
  const weekdays = weekdayLabels()

  return (
    <div
      role="grid"
      aria-label={`Economic calendar, ${grid.label}`}
      className="hidden min-w-0 overflow-hidden rounded-xl border border-border bg-card md:block"
    >
      <div role="row" className="grid grid-cols-7 border-b border-border">
        {weekdays.map((weekday) => (
          <div
            key={weekday}
            role="columnheader"
            className="px-2 py-2 text-center text-[11px] font-medium uppercase tracking-wide text-muted-foreground"
          >
            {weekday}
          </div>
        ))}
      </div>

      {grid.weeks.map((week) => (
        <div
          key={week.key}
          role="row"
          className="grid grid-cols-7 border-b border-border last:border-b-0"
        >
          {week.days.map((day) => (
            <CalendarDayCell
              key={day.key}
              day={day}
              timeZone={timeZone}
              isSubscribed={isSubscribed}
              onSelectEvent={onSelectEvent}
            />
          ))}
        </div>
      ))}
    </div>
  )
}
