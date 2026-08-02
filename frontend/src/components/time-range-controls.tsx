import { Button } from '@/components/ui/button'
import {
  TIME_RANGE_OPTIONS,
  usePreferencesStore,
} from '@/stores/preferences-store'

export function TimeRangePicker() {
  const timeRange = usePreferencesStore((state) => state.timeRange)
  const setTimeRange = usePreferencesStore((state) => state.setTimeRange)

  return (
    <div className="flex flex-col items-center gap-3">
      <p className="text-sm text-muted-foreground">Time range</p>
      <div className="flex flex-wrap items-center justify-center gap-2">
        {TIME_RANGE_OPTIONS.map((option) => (
          <Button
            key={option.value}
            type="button"
            size="sm"
            variant={timeRange === option.value ? 'default' : 'outline'}
            aria-pressed={timeRange === option.value}
            onClick={() => setTimeRange(option.value)}
          >
            {option.label}
          </Button>
        ))}
      </div>
    </div>
  )
}

export function TimeRangeBadge() {
  const timeRange = usePreferencesStore((state) => state.timeRange)

  return (
    <p className="rounded-md border px-3 py-1.5 text-sm text-muted-foreground">
      Showing data for{' '}
      <span className="font-medium text-foreground">{timeRange}</span>
    </p>
  )
}
