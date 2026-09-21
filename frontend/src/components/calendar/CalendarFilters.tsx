import {
  EVENT_TYPE_FILTER_OPTIONS,
  IMPACT_LEVEL_FILTER_OPTIONS,
} from '@/constants/economicCalendar'
import { cn } from '@/lib/utils'
import type {
  EventTypeFilter,
  ImpactLevelFilter,
} from '@/types/economicCalendar'

const SELECT_CLASSES = cn(
  'h-9 w-full min-w-0 rounded-md border border-input bg-transparent px-2 text-sm sm:w-auto',
  'touch-manipulation outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50',
  'dark:bg-input/30',
)

type CalendarFiltersProps = {
  eventType: EventTypeFilter
  onEventTypeChange: (value: EventTypeFilter) => void
  impactLevel: ImpactLevelFilter
  onImpactLevelChange: (value: ImpactLevelFilter) => void
}

export function CalendarFilters({
  eventType,
  onEventTypeChange,
  impactLevel,
  onImpactLevelChange,
}: CalendarFiltersProps) {
  return (
    <div className="flex min-w-0 flex-col gap-2 sm:flex-row sm:items-center">
      <select
        aria-label="Event type filter"
        value={eventType}
        onChange={(event) =>
          onEventTypeChange(event.target.value as EventTypeFilter)
        }
        className={SELECT_CLASSES}
      >
        {EVENT_TYPE_FILTER_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      <select
        aria-label="Impact level filter"
        value={impactLevel}
        onChange={(event) =>
          onImpactLevelChange(event.target.value as ImpactLevelFilter)
        }
        className={SELECT_CLASSES}
      >
        {IMPACT_LEVEL_FILTER_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
}
