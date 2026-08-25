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
    <div className="min-w-0 overflow-x-auto rounded-xl border border-border">
      <table className="w-full min-w-0 text-left text-sm">
        <caption className="sr-only">Historical indicator observations</caption>
        <thead className="bg-muted/50 text-xs uppercase tracking-wider text-muted-foreground">
          <tr>
            <th className="px-3 py-2 font-medium">Date</th>
            <th className="px-3 py-2 font-medium">Indicator</th>
            <th className="px-3 py-2 font-medium">Value</th>
            <th className="px-3 py-2 font-medium">Change</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={`${row.indicator_name}-${row.time}`}
              className="border-t border-border"
            >
              <td className="whitespace-nowrap px-3 py-2 tabular-nums text-muted-foreground">
                {formatIndicatorTimestamp(row.time)}
              </td>
              <td className="px-3 py-2 uppercase">
                {formatIndicatorTitle(row.indicator_name)}
              </td>
              <td className="px-3 py-2 tabular-nums">
                {row.current_value.toFixed(2)}
              </td>
              <td className="px-3 py-2">
                <MacroIndicatorImpact
                  indicatorName={row.indicator_name}
                  changePercent={row.change_percent}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
