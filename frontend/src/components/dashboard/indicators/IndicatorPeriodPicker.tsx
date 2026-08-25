import { Button } from '@/components/ui/button'
import { INDICATOR_HISTORY_PERIODS } from '@/api/macroIndicators'
import type { MacroIndicatorPeriod } from '@/types/macroIndicators'

type IndicatorPeriodPickerProps = {
  value: MacroIndicatorPeriod
  onChange: (period: MacroIndicatorPeriod) => void
}

export function IndicatorPeriodPicker({
  value,
  onChange,
}: IndicatorPeriodPickerProps) {
  return (
    <div
      className="flex w-full min-w-0 flex-wrap items-center gap-1.5 sm:w-auto sm:gap-2"
      role="group"
      aria-label="Historical period"
    >
      {INDICATOR_HISTORY_PERIODS.map((option) => (
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
