import { usePreferencesStore } from '@/stores/preferencesStore'

export function TimeRangeBadge() {
  const timeRange = usePreferencesStore((state) => state.timeRange)

  return (
    <p className="w-full rounded-md border px-3 py-1.5 text-sm text-muted-foreground sm:w-auto">
      Showing data for{' '}
      <span className="font-medium text-foreground">{timeRange}</span>
    </p>
  )
}
