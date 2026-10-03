import { MarketConditionIcon } from '@/components/dashboard/predictions/accuracy/MarketConditionIcon'
import {
  formatAccuracyPercent,
  formatErrorPercent,
  formatSampleCount,
  marketAccuracy,
  marketConditionLabel,
  marketGradeBarClass,
  marketGradeTextClass,
} from '@/lib/predictionAccuracy'
import { cn } from '@/lib/utils'
import type { MarketBreakdownRow, MarketGrade } from '@/types/predictionAccuracy'

type PredictionAccuracyMarketTileProps = {
  row: MarketBreakdownRow
  grade: MarketGrade | null
}

/**
 * One market at a glance: its price accuracy, coloured by grade, with a bar
 * on the same 0–100% scale so markets can be compared by length.
 */
export function PredictionAccuracyMarketTile({
  row,
  grade,
}: PredictionAccuracyMarketTileProps) {
  const label = marketConditionLabel(row.condition)
  const accuracy = marketAccuracy(row.mape)

  return (
    <li
      role="group"
      aria-label={label}
      className="flex min-w-0 flex-col gap-1.5 rounded-md border p-2.5"
    >
      <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <MarketConditionIcon condition={row.condition} />
        <span className="truncate">{label}</span>
      </span>
      <span
        className={cn(
          'font-mono text-lg font-semibold tabular-nums',
          marketGradeTextClass(grade) || 'text-foreground',
        )}
      >
        {formatAccuracyPercent(accuracy)}
      </span>
      <span aria-hidden="true" className="h-1.5 w-full rounded-full bg-muted">
        <span
          className={cn('block h-full rounded-full', marketGradeBarClass(grade))}
          style={{ width: `${accuracy ?? 0}%` }}
        />
      </span>
      <span className="text-[11px] text-muted-foreground">
        {formatErrorPercent(row.mape)} miss · {formatSampleCount(row.samples)}{' '}
        forecasts
      </span>
    </li>
  )
}
