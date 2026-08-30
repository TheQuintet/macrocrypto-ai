import { ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { indicatorSeriesColor } from '@/lib/indicatorSeriesColor'
import { cn } from '@/lib/utils'
import type { IndicatorHistoryFilter } from '@/types/macroIndicators'

const INDICATOR_FILTER_OPTIONS: {
  value: IndicatorHistoryFilter
  label: string
}[] = [
  { value: 'all', label: 'All' },
  { value: 'cpi', label: 'CPI' },
  { value: 'federal_funds_rate', label: 'Fed funds' },
  { value: 'gdp', label: 'GDP' },
]

type IndicatorHistoryFilterProps = {
  value: IndicatorHistoryFilter
  onChange: (value: IndicatorHistoryFilter) => void
}

export function IndicatorHistoryFilter({
  value,
  onChange,
}: IndicatorHistoryFilterProps) {
  const seriesColor =
    value === 'all' ? undefined : indicatorSeriesColor(value)

  return (
    <div className="w-full min-w-0 sm:w-auto">
      <div className="relative sm:hidden">
        {seriesColor ? (
          <span
            aria-hidden
            className="pointer-events-none absolute top-1/2 left-3 size-2.5 -translate-y-1/2 rounded-full"
            style={{ backgroundColor: seriesColor }}
          />
        ) : null}
        <select
          aria-label="Indicator filter"
          value={value}
          onChange={(event) =>
            onChange(event.target.value as IndicatorHistoryFilter)
          }
          className={cn(
            'h-11 w-full min-w-0 appearance-none rounded-lg border border-input bg-transparent py-1 pr-9 text-base touch-manipulation',
            'outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50',
            'dark:bg-input/30',
            seriesColor ? 'pl-8' : 'pl-3',
          )}
        >
          {INDICATOR_FILTER_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDown
          aria-hidden
          className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-muted-foreground"
        />
      </div>

      <div
        className="hidden flex-wrap items-center justify-end gap-2 sm:flex"
        role="group"
        aria-label="Indicator filter"
      >
        {INDICATOR_FILTER_OPTIONS.map((option) => (
          <Button
            key={option.value}
            type="button"
            size="sm"
            variant={value === option.value ? 'default' : 'outline'}
            aria-pressed={value === option.value}
            className="min-h-7 touch-manipulation"
            onClick={() => onChange(option.value)}
          >
            {option.value === 'all' ? null : (
              <span
                aria-hidden
                className="size-2 shrink-0 rounded-full"
                style={{ backgroundColor: indicatorSeriesColor(option.value) }}
              />
            )}
            {option.label}
          </Button>
        ))}
      </div>
    </div>
  )
}
