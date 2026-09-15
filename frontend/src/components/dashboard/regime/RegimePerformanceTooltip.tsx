import {
  formatPercent,
  formatRatio,
  formatRegimePrice,
  formatRegimeRange,
  returnToneClass,
} from '@/lib/regimePerformance'
import { regimeDisplay } from '@/lib/regimeDisplay'
import { cn } from '@/lib/utils'
import type { RegimePerformanceRow } from '@/types/regime'

type RegimePerformanceTooltipProps = {
  row: RegimePerformanceRow
}

/** Every metric for one regime — the hover detail behind the bar chart. */
export function RegimePerformanceTooltip({
  row,
}: RegimePerformanceTooltipProps) {
  const display = regimeDisplay(row.regimeType, 'neutral')
  const metrics = row.performance

  return (
    <div className="flex min-w-0 flex-col gap-1.5 rounded-md border border-border bg-popover p-2.5 text-xs text-popover-foreground shadow-md">
      <div className="flex flex-col gap-0.5">
        <span className="font-medium">{display.label}</span>
        <span className="text-muted-foreground">
          {formatRegimeRange(row.startDate, row.endDate)}
          {row.status === 'active' ? ' · current' : ''}
        </span>
      </div>

      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5">
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

        <dt className="text-muted-foreground">BTC</dt>
        <dd className="text-right tabular-nums">
          {formatRegimePrice(metrics.btcPriceStart)} →{' '}
          {formatRegimePrice(metrics.btcPriceEnd)}
        </dd>
      </dl>
    </div>
  )
}
