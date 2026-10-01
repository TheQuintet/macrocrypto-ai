import { MarketConditionIcon } from '@/components/dashboard/predictions/accuracy/MarketConditionIcon'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  formatAccuracyPercent,
  formatErrorPercent,
  formatSampleCount,
  formatUsdMiss,
  marketAccuracy,
  marketConditionLabel,
  marketGrade,
  marketGradeLegend,
  marketGradeTextClass,
} from '@/lib/predictionAccuracy'
import { cn } from '@/lib/utils'
import type {
  AccuracyThreshold,
  MarketBreakdownRow,
} from '@/types/predictionAccuracy'

type PredictionAccuracyBreakdownTableProps = {
  rows: MarketBreakdownRow[]
  /** The model's MAPE across every market, the yellow line. */
  overallMape: number | null
  /** The service's MAPE check, the red line. */
  mapeThreshold: AccuracyThreshold | undefined
}

/**
 * How accurate, and how far off, the model was in each kind of market,
 * graded the same way as the tiles on the card.
 */
export function PredictionAccuracyBreakdownTable({
  rows,
  overallMape,
  mapeThreshold,
}: PredictionAccuracyBreakdownTableProps) {
  if (rows.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No market-condition breakdown for this window yet.
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      <Table aria-label="Accuracy by market condition">
        <TableHeader>
          <TableRow>
            <TableHead>Market</TableHead>
            <TableHead className="text-right">Accuracy</TableHead>
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
                  <MarketConditionIcon condition={row.condition} />
                  {marketConditionLabel(row.condition)}
                </span>
              </TableCell>
              <TableCell
                className={cn(
                  'text-right tabular-nums',
                  marketGradeTextClass(
                    marketGrade(row.mape, overallMape, mapeThreshold),
                  ),
                )}
              >
                {formatAccuracyPercent(marketAccuracy(row.mape))}
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
      <p className="text-xs text-muted-foreground">
        {marketGradeLegend(mapeThreshold)}
      </p>
    </div>
  )
}
