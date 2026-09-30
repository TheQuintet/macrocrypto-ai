import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  formatErrorPercent,
  formatSampleCount,
  formatUsdMiss,
  marketConditionDotClass,
  marketConditionLabel,
} from '@/lib/predictionAccuracy'
import { cn } from '@/lib/utils'
import type { MarketBreakdownRow } from '@/types/predictionAccuracy'

type PredictionAccuracyBreakdownTableProps = {
  rows: MarketBreakdownRow[]
}

/** How far off the model was in each kind of market. */
export function PredictionAccuracyBreakdownTable({
  rows,
}: PredictionAccuracyBreakdownTableProps) {
  if (rows.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No market-condition breakdown for this window yet.
      </p>
    )
  }

  return (
    <Table aria-label="Accuracy by market condition">
      <TableHeader>
        <TableRow>
          <TableHead>Market</TableHead>
          <TableHead className="text-right">Typical miss</TableHead>
          <TableHead className="text-right">Avg % miss</TableHead>
          <TableHead className="text-right">Forecasts</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={row.condition}>
            <TableCell>
              <span className="flex items-center gap-2">
                <span
                  aria-hidden="true"
                  className={cn(
                    'size-2 shrink-0 rounded-full',
                    marketConditionDotClass(row.condition),
                  )}
                />
                {marketConditionLabel(row.condition)}
              </span>
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {formatUsdMiss(row.mae)}
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {formatErrorPercent(row.mape)}
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {formatSampleCount(row.samples)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
