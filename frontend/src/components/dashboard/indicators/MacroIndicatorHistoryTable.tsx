import { MacroIndicatorImpact } from '@/components/dashboard/indicators/MacroIndicatorImpact'
import {
  formatIndicatorTimestamp,
  formatIndicatorTitle,
} from '@/lib/macroIndicatorHistory'
import type { MacroIndicator } from '@/types/macroIndicators'

type MacroIndicatorHistoryTableProps = {
  indicators: MacroIndicator[]
}

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
      <div className="hidden bg-muted/50 px-3 py-2 text-xs uppercase tracking-wider text-muted-foreground sm:grid sm:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)_auto_auto] sm:gap-3">
        <span>Date</span>
        <span>Indicator</span>
        <span>Value</span>
        <span>Change</span>
      </div>
      {rows.map((row) => (
        <div
          key={`${row.indicator_name}-${row.time}`}
          className="grid grid-cols-1 gap-1 border-t border-border px-3 py-3 sm:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)_auto_auto] sm:items-center sm:gap-3 sm:py-2"
        >
          <span className="min-w-0 text-xs tabular-nums text-muted-foreground sm:text-sm">
            {formatIndicatorTimestamp(row.time)}
          </span>
          <span className="min-w-0 text-sm font-medium uppercase">
            {formatIndicatorTitle(row.indicator_name)}
          </span>
          <span className="min-w-0 text-sm tabular-nums">
            {row.current_value.toFixed(2)}
          </span>
          <div className="-ml-1.5 min-w-0 sm:ml-0 sm:justify-self-end">
            <MacroIndicatorImpact
              indicatorName={row.indicator_name}
              changePercent={row.change_percent}
            />
          </div>
        </div>
      ))}
    </div>
  )
}
