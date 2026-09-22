import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { CalendarFilters } from '@/components/calendar/CalendarFilters'
import { CalendarTimezoneSelect } from '@/components/calendar/CalendarTimezoneSelect'
import type {
  CalendarTimezoneMode,
  CalendarViewMode,
  EventTypeFilter,
  ImpactLevelFilter,
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
  eventType: EventTypeFilter
  onEventTypeChange: (value: EventTypeFilter) => void
  impactLevel: ImpactLevelFilter
  onImpactLevelChange: (value: ImpactLevelFilter) => void
  onPrevious: () => void
  onNext: () => void
  isSimulated?: boolean
}

export function CalendarToolbar({
  label,
  view,
  onViewChange,
  timezoneMode,
  onTimezoneModeChange,
  timeZone,
  eventType,
  onEventTypeChange,
  impactLevel,
  onImpactLevelChange,
  onPrevious,
  onNext,
  isSimulated = false,
}: CalendarToolbarProps) {
  return (
    <div className="flex min-w-0 flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex min-w-0 items-center gap-1.5">
        <Button
          type="button"
          size="icon"
          variant="ghost"
          aria-label={`Previous ${view}`}
          onClick={onPrevious}
        >
          <ChevronLeft aria-hidden className="size-5" />
        </Button>
        <Button
          type="button"
          size="icon"
          variant="ghost"
          aria-label={`Next ${view}`}
          onClick={onNext}
        >
          <ChevronRight aria-hidden className="size-5" />
        </Button>
        <h2 className="min-w-0 truncate px-1 text-lg font-semibold tracking-tight sm:text-xl">
          {label}
        </h2>
        {isSimulated ? (
          <Badge
            variant="outline"
            className="hidden shrink-0 text-[10px] font-normal sm:inline-flex"
          >
            Simulated
          </Badge>
        ) : null}
      </div>

      <div className="flex min-w-0 flex-wrap items-center gap-2">
        <div
          role="group"
          aria-label="Calendar view"
          className="flex items-center rounded-md border border-border p-0.5"
        >
          {VIEW_OPTIONS.map((option) => (
            <Button
              key={option.value}
              type="button"
              size="sm"
              variant={view === option.value ? 'default' : 'ghost'}
              aria-pressed={view === option.value}
              className="h-7 min-h-7 px-2.5 text-xs touch-manipulation"
              onClick={() => onViewChange(option.value)}
            >
              {option.label}
            </Button>
          ))}
        </div>

        <CalendarFilters
          eventType={eventType}
          onEventTypeChange={onEventTypeChange}
          impactLevel={impactLevel}
          onImpactLevelChange={onImpactLevelChange}
        />

        <CalendarTimezoneSelect
          value={timezoneMode}
          onChange={onTimezoneModeChange}
          timeZone={timeZone}
        />
      </div>
    </div>
  )
}
