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
      className="flex flex-wrap items-center gap-2"
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
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </Button>
      ))}
    </div>
  )
}
