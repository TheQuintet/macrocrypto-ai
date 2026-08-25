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
        <CardTitle className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
          {formatIndicatorTitle(indicator.indicator_name)}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline justify-between gap-2">
          <span className="text-2xl font-bold tabular-nums">
            {indicator.current_value.toFixed(2)}
          </span>
          <MacroIndicatorImpact
            indicatorName={indicator.indicator_name}
            changePercent={indicator.change_percent}
          />
        </div>
        <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
          <span>Previous: {indicator.previous_value?.toFixed(2) ?? '--'}</span>
          <span>Updated: {formatIndicatorTimestamp(indicator.time)}</span>
        </div>
      </CardContent>
    </Card>
  )
}
