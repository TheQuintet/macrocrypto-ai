import { SimilarPeriodConfidence } from '@/components/dashboard/regime/SimilarPeriodConfidence'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { formatIndicatorTitle } from '@/lib/macroIndicatorHistory'
import {
  formatPercent,
  formatRegimePrice,
  formatRegimeRange,
  returnToneClass,
} from '@/lib/regimePerformance'
import { cn } from '@/lib/utils'
import type { SimilarPeriod } from '@/types/regime'

type SimilarPeriodDetailsDialogProps = {
  period: SimilarPeriod | null
  /** Today's prints, so the reader can compare rather than take it on trust. */
  currentConditions: Record<string, number>
  onClose: () => void
}

/** Why this period matched, and what BTC did through it. */
export function SimilarPeriodDetailsDialog({
  period,
  currentConditions,
  onClose,
}: SimilarPeriodDetailsDialogProps) {
  if (!period) {
    return null
  }

  const btc = period.btcPerformance
  const conditions = Object.entries(period.macroConditions)

  return (
    <Dialog open onOpenChange={(open) => (open ? undefined : onClose())}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {formatRegimeRange(period.periodStart, period.periodEnd)}
          </DialogTitle>
          <DialogDescription>{period.reason}</DialogDescription>
        </DialogHeader>

        <SimilarPeriodConfidence score={period.similarityScore} />

        {conditions.length > 0 ? (
          <div className="flex min-w-0 flex-col gap-1.5">
            <h3 className="text-xs font-medium text-muted-foreground">
              Macro conditions, then vs now
            </h3>
            <dl className="grid grid-cols-[1fr_auto_auto] gap-x-4 gap-y-1 text-sm">
              <span className="sr-only">Indicator</span>
              <span className="text-right text-xs text-muted-foreground">
                Then
              </span>
              <span className="text-right text-xs text-muted-foreground">
                Now
              </span>
              {conditions.map(([indicator, value]) => (
                <div key={indicator} className="contents">
                  <dt className="min-w-0 truncate text-muted-foreground">
                    {formatIndicatorTitle(indicator)}
                  </dt>
                  <dd className="text-right tabular-nums">
                    {value.toFixed(2)}
                  </dd>
                  <dd className="text-right tabular-nums text-muted-foreground">
                    {currentConditions[indicator] != null
                      ? currentConditions[indicator].toFixed(2)
                      : '—'}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        ) : null}

        {btc ? (
          <div className="flex min-w-0 flex-col gap-1.5">
            <h3 className="text-xs font-medium text-muted-foreground">
              BTC through this period
            </h3>
            <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 text-sm">
              <dt className="text-muted-foreground">Return</dt>
              <dd
                className={cn(
                  'text-right tabular-nums',
                  returnToneClass(btc.returnPercent),
                )}
              >
                {formatPercent(btc.returnPercent)}
              </dd>

              <dt className="text-muted-foreground">Price</dt>
              <dd className="text-right tabular-nums">
                {formatRegimePrice(btc.priceStart)} →{' '}
                {formatRegimePrice(btc.priceEnd)}
              </dd>

              <dt className="text-muted-foreground">Observations</dt>
              <dd className="text-right tabular-nums">{btc.observations}</dd>
            </dl>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            BTC did not trade far enough back to measure this period.
          </p>
        )}
      </DialogContent>
    </Dialog>
  )
}
