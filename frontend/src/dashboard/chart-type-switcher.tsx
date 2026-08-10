import { Button } from '@/components/ui/button'

export type ChartType = 'line' | 'bar'

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
      className="flex flex-wrap items-center gap-2"
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
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </Button>
      ))}
    </div>
  )
}
