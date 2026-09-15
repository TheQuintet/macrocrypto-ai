import { SimilarPeriodConfidence } from '@/components/dashboard/regime/SimilarPeriodConfidence'
import { Card, CardContent } from '@/components/ui/card'
import {
  formatPercent,
  formatRegimeRange,
  returnToneClass,
} from '@/lib/regimePerformance'
import { cn } from '@/lib/utils'
import type { SimilarPeriod } from '@/types/regime'

type SimilarPeriodCardProps = {
  period: SimilarPeriod
  onSelect: (periodId: string) => void
}

/** One historical parallel — dates, how close it is, why, and what BTC did. */
export function SimilarPeriodCard({
  period,
  onSelect,
}: SimilarPeriodCardProps) {
  const range = formatRegimeRange(period.periodStart, period.periodEnd)
  const btcReturn = period.btcPerformance?.returnPercent ?? null

  return (
    <Card className="min-w-0 py-0 transition-shadow hover:shadow-md">
      <CardContent className="p-0">
        <button
          type="button"
          data-similar-period={period.id}
          aria-label={`${range}, view details`}
          onClick={() => onSelect(period.id)}
          className={cn(
            'flex w-full min-w-0 cursor-pointer flex-col gap-2.5 p-3 text-left',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60',
          )}
        >
          <div className="flex min-w-0 flex-wrap items-baseline justify-between gap-x-2 gap-y-1">
            <span className="min-w-0 truncate text-sm font-medium">
              {range}
            </span>
            <span
              className={cn(
                'text-sm font-medium tabular-nums',
                returnToneClass(btcReturn),
              )}
            >
              {btcReturn == null ? 'BTC —' : `BTC ${formatPercent(btcReturn)}`}
            </span>
          </div>

          <p className="text-xs leading-relaxed text-muted-foreground">
            {period.reason}
          </p>

          <SimilarPeriodConfidence score={period.similarityScore} />
        </button>
      </CardContent>
    </Card>
  )
}
