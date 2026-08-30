import { Button } from '@/components/ui/button'
import { CANDLE_INTERVAL_OPTIONS } from '@/components/dashboard/lib/chartInterval'
import { usePreferencesStore } from '@/stores/preferencesStore'

export function ChartIntervalSwitcher() {
  const candleInterval = usePreferencesStore((state) => state.candleInterval)
  const setCandleInterval = usePreferencesStore(
    (state) => state.setCandleInterval,
  )

  return (
    <div
      className="flex w-full min-w-0 flex-wrap items-center justify-start gap-1.5 sm:w-auto sm:justify-end sm:gap-2"
      role="group"
      aria-label="Chart interval"
    >
      {CANDLE_INTERVAL_OPTIONS.map((option) => (
        <Button
          key={option.value}
          type="button"
          size="sm"
          variant={candleInterval === option.value ? 'default' : 'outline'}
          aria-pressed={candleInterval === option.value}
          className="min-h-11 min-w-10 flex-1 touch-manipulation sm:min-h-7 sm:flex-none"
          onClick={() => setCandleInterval(option.value)}
        >
          {option.label}
        </Button>
      ))}
    </div>
  )
}
