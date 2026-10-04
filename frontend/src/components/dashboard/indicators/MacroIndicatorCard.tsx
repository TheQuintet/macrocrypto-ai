import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { MacroIndicatorImpact } from '@/components/dashboard/indicators/MacroIndicatorImpact'
import { indicatorSeriesColor } from '@/lib/indicatorSeriesColor'
import {
  formatIndicatorCardTitle,
  formatIndicatorValue,
} from '@/lib/macroIndicatorDisplay'
import { formatIndicatorTimestamp } from '@/lib/macroIndicatorHistory'
import type { MacroIndicator } from '@/types/macroIndicators'

type MacroIndicatorCardProps = {
  indicator: MacroIndicator
}

export function MacroIndicatorCard({ indicator }: MacroIndicatorCardProps) {
  const seriesColor = indicatorSeriesColor(indicator.indicator_name)

  return (
    <Card
      data-indicator={indicator.indicator_name}
      className="min-w-0 overflow-hidden border-l-[3px] transition-all hover:shadow-md"
      style={{ borderLeftColor: seriesColor }}
    >
      <CardHeader className="pb-2">
        <CardTitle
          className="text-xs font-medium tracking-wider sm:text-sm"
          style={{ color: seriesColor }}
        >
          {formatIndicatorCardTitle(indicator.indicator_name)}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex min-w-0 flex-wrap items-center justify-between gap-x-2 gap-y-1">
          <span className="min-w-0 text-xl font-bold tabular-nums sm:text-2xl">
            {formatIndicatorValue(
              indicator.current_value,
              indicator.indicator_name,
            )}
          </span>
          <MacroIndicatorImpact
            indicatorName={indicator.indicator_name}
            changePercent={indicator.change_percent}
          />
        </div>
        <div className="mt-2 flex min-w-0 flex-col gap-0.5 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <span>
            Previous:{' '}
            {formatIndicatorValue(
              indicator.previous_value,
              indicator.indicator_name,
            )}
          </span>
          <span>Updated: {formatIndicatorTimestamp(indicator.time)}</span>
        </div>
      </CardContent>
    </Card>
  )
}
