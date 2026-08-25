import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { MacroIndicatorHistoryChart } from '@/components/dashboard/indicators/MacroIndicatorHistoryChart'
import { MacroIndicatorImpact } from '@/components/dashboard/indicators/MacroIndicatorImpact'
import { formatIndicatorTitle } from '@/lib/macroIndicatorHistory'
import type { MacroIndicatorSeries } from '@/types/macroIndicators'

type MacroIndicatorHistoryCardProps = {
  series: MacroIndicatorSeries
}

export function MacroIndicatorHistoryCard({
  series,
}: MacroIndicatorHistoryCardProps) {
  const { latest, points, name } = series
  const title = formatIndicatorTitle(name)

  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
            {title}
          </CardTitle>
          <MacroIndicatorImpact
            indicatorName={name}
            changePercent={latest.change_percent}
          />
        </div>
        <p className="text-xl font-bold tabular-nums sm:text-2xl">
          {latest.current_value.toFixed(2)}
        </p>
      </CardHeader>
      <CardContent>
        <MacroIndicatorHistoryChart points={points} indicatorName={title} />
      </CardContent>
    </Card>
  )
}
