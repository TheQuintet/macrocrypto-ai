import { cn } from '@/lib/utils'
import type { CalendarTimezoneMode } from '@/types/economicCalendar'

type CalendarTimezoneSelectProps = {
  value: CalendarTimezoneMode
  onChange: (mode: CalendarTimezoneMode) => void
  /** Resolved IANA zone, shown so the times on screen are never ambiguous. */
  timeZone: string
}

/**
 * Switches every date on the calendar between the reader's own zone and UTC.
 * Shared by the upcoming grid and the past-events table so both agree.
 */
export function CalendarTimezoneSelect({
  value,
  onChange,
  timeZone,
}: CalendarTimezoneSelectProps) {
  return (
    <div className="flex items-center gap-2">
      <label
        htmlFor="calendar-timezone"
        className="text-xs text-muted-foreground"
      >
        Times in
      </label>
      <select
        id="calendar-timezone"
        value={value}
        onChange={(event) =>
          onChange(event.target.value as CalendarTimezoneMode)
        }
        className={cn(
          'h-8 min-w-0 rounded-md border border-input bg-transparent px-2 text-xs',
          'outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50',
          'dark:bg-input/30',
        )}
      >
        <option value="local">{timeZone}</option>
        <option value="utc">UTC</option>
      </select>
    </div>
  )
}
