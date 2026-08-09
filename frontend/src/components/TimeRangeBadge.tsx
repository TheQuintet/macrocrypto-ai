import { usePreferencesStore } from '@/stores/preferences-store'

export function TimeRangeBadge() {
  const timeRange = usePreferencesStore((state) => state.timeRange)

  return (
    <p className="rounded-md border px-3 py-1.5 text-sm text-muted-foreground">
      Showing data for{' '}
      <span className="font-medium text-foreground">{timeRange}</span>
    </p>
  )
}
