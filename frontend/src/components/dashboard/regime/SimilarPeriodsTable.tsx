import { SimilarPeriodConfidence } from '@/components/dashboard/regime/SimilarPeriodConfidence'
import { SimilarPeriodIndicatorLabel } from '@/components/dashboard/regime/SimilarPeriodIndicatorLabel'
import { SimilarPeriodTodayRow } from '@/components/dashboard/regime/SimilarPeriodTodayRow'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  formatPercent,
  formatRegimeRange,
  returnToneClass,
} from '@/lib/regimePerformance'
import {
  formatConditionValue,
  similarPeriodIndicatorKeys,
} from '@/lib/similarPeriodIndicators'
import { cn } from '@/lib/utils'
import type { SimilarPeriod } from '@/types/regime'

type SimilarPeriodsTableProps = {
  periods: SimilarPeriod[]
  currentConditions: Record<string, number>
  onSelect: (periodId: string) => void
}

/** Today plus each historical match, one row per window, same columns. */
export function SimilarPeriodsTable({
  periods,
  currentConditions,
  onSelect,
}: SimilarPeriodsTableProps) {
  const indicators = similarPeriodIndicatorKeys(currentConditions, periods)

  return (
    <div className="min-w-0 overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Period</TableHead>
            <TableHead className="w-[8.5rem]">Match</TableHead>
            <TableHead className="text-right">BTC return</TableHead>
            {indicators.map((indicator) => (
              <TableHead key={indicator} className="text-right">
                <SimilarPeriodIndicatorLabel
                  name={indicator}
                  className="justify-end text-xs"
                />
              </TableHead>
            ))}
            <TableHead className="hidden sm:table-cell">Why</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <SimilarPeriodTodayRow
            conditions={currentConditions}
            indicators={indicators}
          />
          {periods.map((period) => {
            const range = formatRegimeRange(
              period.periodStart,
              period.periodEnd,
            )
            const btcReturn = period.btcPerformance?.returnPercent ?? null
            const matching = new Set(
              period.matchingIndicators.map((item) => item.indicator),
            )

            return (
              <TableRow
                key={period.id}
                data-similar-period={period.id}
                tabIndex={0}
                aria-label={`${range}, view details`}
                className="cursor-pointer"
                onClick={() => onSelect(period.id)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault()
                    onSelect(period.id)
                  }
                }}
              >
                <TableCell className="min-w-0 font-medium">
                  <span className="whitespace-nowrap">{range}</span>
                  <span className="mt-1 block text-xs font-normal text-muted-foreground sm:hidden">
                    {period.reason}
                  </span>
                </TableCell>
                <TableCell>
                  <SimilarPeriodConfidence score={period.similarityScore} />
                </TableCell>
                <TableCell
                  className={cn(
                    'text-right font-medium tabular-nums',
                    returnToneClass(btcReturn),
                  )}
                >
                  {btcReturn == null
                    ? 'BTC —'
                    : `BTC ${formatPercent(btcReturn)}`}
                </TableCell>
                {indicators.map((indicator) => (
                  <TableCell
                    key={indicator}
                    data-indicator={indicator}
                    className={cn(
                      'text-right tabular-nums',
                      matching.has(indicator)
                        ? 'font-medium'
                        : 'text-muted-foreground',
                    )}
                  >
                    {formatConditionValue(period.macroConditions[indicator])}
                  </TableCell>
                ))}
                <TableCell className="hidden max-w-sm text-muted-foreground sm:table-cell">
                  {period.reason}
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}
