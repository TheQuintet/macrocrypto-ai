import { Button } from '@/components/ui/button'
import { CHART_INTERVAL_OPTIONS } from '@/components/dashboard/lib/chartInterval'
import type { ChartInterval } from '@/types/chart'

type ChartIntervalSwitcherProps = {
  value: ChartInterval
  onChange: (value: ChartInterval) => void
}

export function ChartIntervalSwitcher({
  value,
  onChange,
}: ChartIntervalSwitcherProps) {
  return (
    <div
      className="flex w-full min-w-0 flex-wrap items-center gap-1.5 sm:w-auto sm:gap-2"
      role="group"
      aria-label="Chart interval"
    >
      {CHART_INTERVAL_OPTIONS.map((option) => (
        <Button
          key={option.value}
          type="button"
          size="sm"
          variant={value === option.value ? 'default' : 'outline'}
          aria-pressed={value === option.value}
          className="min-h-11 min-w-10 flex-1 touch-manipulation sm:min-h-7 sm:flex-none"
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </Button>
      ))}
    </div>
  )
}
