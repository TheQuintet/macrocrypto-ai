import { MacroIndicatorImpact } from '@/components/dashboard/indicators/MacroIndicatorImpact'
import { indicatorSeriesColor } from '@/lib/indicatorSeriesColor'
import {
  formatIndicatorTimestamp,
  formatIndicatorTitle,
} from '@/lib/macroIndicatorHistory'
import { cn } from '@/lib/utils'
import type { MacroIndicator } from '@/types/macroIndicators'

type MacroIndicatorHistoryTableProps = {
  indicators: MacroIndicator[]
}

const HISTORY_TABLE_COLS =
  'sm:grid-cols-[max-content_minmax(0,1fr)_max-content_max-content]'

export function MacroIndicatorHistoryTable({
  indicators,
}: MacroIndicatorHistoryTableProps) {
  const rows = [...indicators].sort(
    (left, right) => Date.parse(right.time) - Date.parse(left.time),
  )

  return (
    <div
      role="region"
      aria-label="Historical indicator observations"
      className="min-w-0 overflow-hidden rounded-xl border border-border"
    >
      <div
        className={cn(
          'hidden border-l-[3px] border-l-transparent bg-muted/50 px-3 py-2 text-xs uppercase tracking-wider text-muted-foreground sm:grid sm:items-center sm:gap-x-6',
          HISTORY_TABLE_COLS,
        )}
      >
        <span>Date</span>
        <span>Indicator</span>
        <span className="text-right">Value</span>
        <span className="text-right">Change</span>
      </div>
      {rows.map((row) => {
        const seriesColor = indicatorSeriesColor(row.indicator_name)

        return (
          <div
            key={`${row.indicator_name}-${row.time}`}
            data-indicator={row.indicator_name}
            className={cn(
              'grid grid-cols-1 gap-1 border-t border-border border-l-[3px] px-3 py-3 sm:items-center sm:gap-x-6 sm:py-2',
              HISTORY_TABLE_COLS,
            )}
            style={{ borderLeftColor: seriesColor }}
          >
            <span className="whitespace-nowrap text-xs tabular-nums text-muted-foreground sm:text-sm">
              {formatIndicatorTimestamp(row.time)}
            </span>
            <span
              className="min-w-0 truncate text-sm font-medium uppercase"
              style={{ color: seriesColor }}
            >
              {formatIndicatorTitle(row.indicator_name)}
            </span>
            <span className="whitespace-nowrap text-sm tabular-nums sm:text-right">
              {row.current_value.toFixed(2)}
            </span>
            <div className="-ml-1.5 sm:ml-0 sm:justify-self-end">
              <MacroIndicatorImpact
                indicatorName={row.indicator_name}
                changePercent={row.change_percent}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
