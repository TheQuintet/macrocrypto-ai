import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type {
  CalendarTimezoneMode,
  CalendarViewMode,
} from '@/types/economicCalendar'

const VIEW_OPTIONS: { value: CalendarViewMode; label: string }[] = [
  { value: 'month', label: 'Month' },
  { value: 'week', label: 'Week' },
]

type CalendarToolbarProps = {
  label: string
  view: CalendarViewMode
  onViewChange: (view: CalendarViewMode) => void
  timezoneMode: CalendarTimezoneMode
  onTimezoneModeChange: (mode: CalendarTimezoneMode) => void
  /** Resolved IANA zone, shown so the times on screen are never ambiguous. */
  timeZone: string
  onPrevious: () => void
  onNext: () => void
  onToday: () => void
}

export function CalendarToolbar({
  label,
  view,
  onViewChange,
  timezoneMode,
  onTimezoneModeChange,
  timeZone,
  onPrevious,
  onNext,
  onToday,
}: CalendarToolbarProps) {
  return (
    <div className="flex min-w-0 flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 items-center gap-2">
        <Button
          type="button"
          size="icon"
          variant="outline"
          aria-label={`Previous ${view}`}
          onClick={onPrevious}
        >
          <ChevronLeft aria-hidden className="size-4" />
        </Button>
        <Button
          type="button"
          size="icon"
          variant="outline"
          aria-label={`Next ${view}`}
          onClick={onNext}
        >
          <ChevronRight aria-hidden className="size-4" />
        </Button>
        <Button type="button" size="sm" variant="outline" onClick={onToday}>
          Today
        </Button>
        <h2 className="min-w-0 truncate text-sm font-medium sm:text-base">
          {label}
        </h2>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div
          role="group"
          aria-label="Calendar view"
          className="flex items-center gap-1"
        >
          {VIEW_OPTIONS.map((option) => (
            <Button
              key={option.value}
              type="button"
              size="sm"
              variant={view === option.value ? 'default' : 'outline'}
              aria-pressed={view === option.value}
              className="min-h-7 touch-manipulation"
              onClick={() => onViewChange(option.value)}
            >
              {option.label}
            </Button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <label
            htmlFor="calendar-timezone"
            className="text-xs text-muted-foreground"
          >
            Times in
          </label>
          <select
            id="calendar-timezone"
            value={timezoneMode}
            onChange={(event) =>
              onTimezoneModeChange(
                event.target.value as CalendarTimezoneMode,
              )
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
      </div>
    </div>
  )
}
