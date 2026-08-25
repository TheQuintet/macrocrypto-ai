import { Button } from '@/components/ui/button'
import type { MacroIndicatorView } from '@/types/macroIndicators'

const VIEW_OPTIONS: { value: MacroIndicatorView; label: string }[] = [
  { value: 'current', label: 'Current' },
  { value: 'historical', label: 'Historical' },
]

type IndicatorViewToggleProps = {
  value: MacroIndicatorView
  onChange: (view: MacroIndicatorView) => void
}

export function IndicatorViewToggle({
  value,
  onChange,
}: IndicatorViewToggleProps) {
  return (
    <div
      className="flex w-full min-w-0 flex-wrap items-center gap-1.5 sm:w-auto sm:gap-2"
      role="group"
      aria-label="Indicator view"
    >
      {VIEW_OPTIONS.map((option) => (
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
