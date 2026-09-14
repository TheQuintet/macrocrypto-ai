import { Button } from '@/components/ui/button'
import type { CalendarEventScope } from '@/types/economicCalendar'

const SCOPE_OPTIONS: { value: CalendarEventScope; label: string }[] = [
  { value: 'upcoming', label: 'Upcoming' },
  { value: 'past', label: 'Past events' },
]

type CalendarScopeToggleProps = {
  value: CalendarEventScope
  onChange: (scope: CalendarEventScope) => void
}

/** Switches the calendar between the grid of what is coming and the table of what has been. */
export function CalendarScopeToggle({
  value,
  onChange,
}: CalendarScopeToggleProps) {
  return (
    <div
      role="group"
      aria-label="Event scope"
      className="flex items-center gap-1"
    >
      {SCOPE_OPTIONS.map((option) => (
        <Button
          key={option.value}
          type="button"
          size="sm"
          variant={value === option.value ? 'default' : 'outline'}
          aria-pressed={value === option.value}
          className="min-h-7 touch-manipulation"
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </Button>
      ))}
    </div>
  )
}
