import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { MacroIndicatorImpact } from '@/components/dashboard/indicators/MacroIndicatorImpact'
import {
  formatIndicatorTimestamp,
  formatIndicatorTitle,
} from '@/lib/macroIndicatorHistory'
import type { MacroIndicator } from '@/types/macroIndicators'

type MacroIndicatorCardProps = {
  indicator: MacroIndicator
}

export function MacroIndicatorCard({ indicator }: MacroIndicatorCardProps) {
  return (
    <Card className="min-w-0 overflow-hidden transition-all hover:shadow-md">
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-medium uppercase tracking-wider text-muted-foreground sm:text-sm">
          {formatIndicatorTitle(indicator.indicator_name)}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex min-w-0 flex-wrap items-center justify-between gap-x-2 gap-y-1">
          <span className="min-w-0 text-xl font-bold tabular-nums sm:text-2xl">
            {indicator.current_value.toFixed(2)}
          </span>
          <MacroIndicatorImpact
            indicatorName={indicator.indicator_name}
            changePercent={indicator.change_percent}
          />
        </div>
        <div className="mt-2 flex min-w-0 flex-col gap-0.5 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <span>Previous: {indicator.previous_value?.toFixed(2) ?? '--'}</span>
          <span>Updated: {formatIndicatorTimestamp(indicator.time)}</span>
        </div>
      </CardContent>
    </Card>
  )
}
