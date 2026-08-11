import { Button } from '@/components/ui/button'
import {
  TIME_RANGE_OPTIONS,
  usePreferencesStore,
} from '@/stores/preferencesStore'

export function TimeRangePicker() {
  const timeRange = usePreferencesStore((state) => state.timeRange)
  const setTimeRange = usePreferencesStore((state) => state.setTimeRange)

  return (
    <div
      className="flex w-full flex-wrap items-center gap-1.5 sm:w-auto sm:gap-2"
      role="group"
      aria-label="Time range"
    >
      {TIME_RANGE_OPTIONS.map((option) => (
        <Button
          key={option.value}
          type="button"
          size="sm"
          variant={timeRange === option.value ? 'default' : 'outline'}
          aria-pressed={timeRange === option.value}
          className="min-w-10 flex-1 sm:flex-none"
          onClick={() => setTimeRange(option.value)}
        >
          {option.label}
        </Button>
      ))}
    </div>
  )
}
