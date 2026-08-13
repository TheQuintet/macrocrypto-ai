import { Button } from '@/components/ui/button'
import type { ChartType } from '@/types/chart'

const CHART_TYPE_OPTIONS: { value: ChartType; label: string }[] = [
  { value: 'line', label: 'Line' },
  { value: 'bar', label: 'Bar' },
]

type ChartTypeSwitcherProps = {
  value: ChartType
  onChange: (value: ChartType) => void
}

export function ChartTypeSwitcher({
  value,
  onChange,
}: ChartTypeSwitcherProps) {
  return (
    <div
      className="flex w-full min-w-0 flex-wrap items-center gap-1.5 sm:w-auto sm:gap-2"
      role="group"
      aria-label="Chart type"
    >
      {CHART_TYPE_OPTIONS.map((option) => (
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
