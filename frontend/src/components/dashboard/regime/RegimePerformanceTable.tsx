import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import {
  formatPercent,
  formatRatio,
  formatRegimeRange,
  returnToneClass,
  sortRegimesByStart,
} from '@/lib/regimePerformance'
import { regimeDisplay } from '@/lib/regimeDisplay'
import { regimeSeriesColor } from '@/lib/regimeSeriesColor'
import { cn } from '@/lib/utils'
import type { RegimePerformanceRow } from '@/types/regime'

type RegimePerformanceTableProps = {
  rows: RegimePerformanceRow[]
}

/** Every metric the chart only hints at, newest regime first. */
export function RegimePerformanceTable({ rows }: RegimePerformanceTableProps) {
  const ordered = sortRegimesByStart(rows).reverse()

  return (
    <div className="min-w-0 overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Regime</TableHead>
            <TableHead className="hidden sm:table-cell">Period</TableHead>
            <TableHead className="text-right">Avg return</TableHead>
            <TableHead className="hidden text-right sm:table-cell">
              Max drawdown
            </TableHead>
            <TableHead className="hidden text-right md:table-cell">
              Volatility
            </TableHead>
            <TableHead className="text-right">Sharpe</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {ordered.map((row) => {
            const display = regimeDisplay(row.regimeType, 'neutral')

            return (
              <TableRow key={row.regimeId} data-regime={row.regimeType}>
                <TableCell className="min-w-0">
                  <div className="flex min-w-0 flex-wrap items-center gap-1.5">
                    <span
                      aria-hidden="true"
                      className="size-2 shrink-0 rounded-full"
                      style={{
                        backgroundColor: regimeSeriesColor(row.regimeType),
                      }}
                    />
                    <span className="truncate font-medium">
                      {display.label}
                    </span>
                    {row.status === 'active' ? (
                      <Badge
                        variant="outline"
                        className="text-[10px] font-normal"
                      >
                        Current
                      </Badge>
                    ) : null}
                  </div>
                  <span className="text-xs text-muted-foreground sm:hidden">
                    {formatRegimeRange(row.startDate, row.endDate)}
                  </span>
                </TableCell>
                <TableCell className="hidden whitespace-nowrap text-muted-foreground sm:table-cell">
                  {formatRegimeRange(row.startDate, row.endDate)}
                </TableCell>
                <TableCell
                  className={cn(
                    'text-right tabular-nums',
                    returnToneClass(row.performance.avgReturn),
                  )}
                >
                  {formatPercent(row.performance.avgReturn)}
                </TableCell>
                <TableCell className="hidden text-right tabular-nums sm:table-cell">
                  {formatPercent(row.performance.maxDrawdown)}
                </TableCell>
                <TableCell className="hidden text-right tabular-nums md:table-cell">
                  {formatPercent(row.performance.volatility)}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatRatio(row.performance.sharpeRatio)}
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}
