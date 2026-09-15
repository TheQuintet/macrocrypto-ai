import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { regimeDisplay } from '@/lib/regimeDisplay'
import { regimeSeriesColor } from '@/lib/regimeSeriesColor'
import {
  formatPercent,
  formatRatio,
  formatRegimePrice,
  formatRegimeRange,
  returnToneClass,
} from '@/lib/regimePerformance'
import { cn } from '@/lib/utils'
import type { RegimeHistoryRow } from '@/types/regime'

type RegimeDetailsDialogProps = {
  regime: RegimeHistoryRow | null
  onClose: () => void
}

/** What a regime was, when it ran, and how BTC did in it. */
export function RegimeDetailsDialog({
  regime,
  onClose,
}: RegimeDetailsDialogProps) {
  if (!regime) {
    return null
  }

  const display = regimeDisplay(regime.regimeType, 'neutral')
  const metrics = regime.performance

  return (
    <Dialog open onOpenChange={(open) => (open ? undefined : onClose())}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex flex-wrap items-center gap-2">
            <span
              aria-hidden="true"
              className="size-2.5 shrink-0 rounded-full"
              style={{ backgroundColor: regimeSeriesColor(regime.regimeType) }}
            />
            {display.label}
            {regime.isCurrent ? (
              <Badge variant="outline" className="text-[10px] font-normal">
                Current
              </Badge>
            ) : null}
          </DialogTitle>
          <DialogDescription>
            {formatRegimeRange(regime.startDate, regime.endDate)}
          </DialogDescription>
        </DialogHeader>

        <p className="text-sm text-muted-foreground">{display.explanation}</p>

        {metrics ? (
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 text-sm">
            <dt className="text-muted-foreground">Avg return</dt>
            <dd
              className={cn(
                'text-right tabular-nums',
                returnToneClass(metrics.avgReturn),
              )}
            >
              {formatPercent(metrics.avgReturn)}
            </dd>

            <dt className="text-muted-foreground">Max drawdown</dt>
            <dd className="text-right tabular-nums">
              {formatPercent(metrics.maxDrawdown)}
            </dd>

            <dt className="text-muted-foreground">Volatility</dt>
            <dd className="text-right tabular-nums">
              {formatPercent(metrics.volatility)}
            </dd>

            <dt className="text-muted-foreground">Sharpe ratio</dt>
            <dd className="text-right tabular-nums">
              {formatRatio(metrics.sharpeRatio)}
            </dd>

            <dt className="text-muted-foreground">BTC start</dt>
            <dd className="text-right tabular-nums">
              {formatRegimePrice(metrics.btcPriceStart)}
            </dd>

            <dt className="text-muted-foreground">BTC end</dt>
            <dd className="text-right tabular-nums">
              {formatRegimePrice(metrics.btcPriceEnd)}
            </dd>
          </dl>
        ) : (
          <p className="text-sm text-muted-foreground">
            {regime.isCurrent
              ? 'Performance is measured once the regime closes.'
              : 'No performance was recorded for this regime.'}
          </p>
        )}
      </DialogContent>
    </Dialog>
  )
}
