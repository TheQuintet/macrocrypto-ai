import { useMemo } from 'react'
import { MacroIndicatorHistoryChart } from '@/components/dashboard/indicators/MacroIndicatorHistoryChart'
import { MacroIndicatorHistoryTable } from '@/components/dashboard/indicators/MacroIndicatorHistoryTable'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { groupIndicatorsByName } from '@/lib/macroIndicatorHistory'
import { cn } from '@/lib/utils'
import type { MacroIndicator } from '@/types/macroIndicators'

type MacroIndicatorHistoryProps = {
  indicators: MacroIndicator[]
  isLoading?: boolean
  error?: Error | null
  className?: string
  includeTable?: boolean
  framed?: boolean
}

export function MacroIndicatorHistory({
  indicators,
  isLoading = false,
  error = null,
  className,
  includeTable = true,
  framed = true,
}: MacroIndicatorHistoryProps) {
  const series = useMemo(
    () => groupIndicatorsByName(indicators),
    [indicators],
  )

  if (isLoading) {
    const skeleton = <Skeleton className="h-56 w-full sm:h-72" />
    return (
      <div className={cn('flex min-w-0 flex-col gap-4', className)}>
        {framed ? (
          <Card className="min-w-0 overflow-hidden">
            <CardContent className="pt-6">{skeleton}</CardContent>
          </Card>
        ) : (
          skeleton
        )}
      </div>
    )
  }

  if (error) {
    return (
      <div className={cn('p-4 text-center text-red-500', className)}>
        <p>Failed to load historical indicator data</p>
        <p className="text-sm text-muted-foreground">{error.message}</p>
      </div>
    )
  }

  if (series.length === 0) {
    return (
      <div className={cn('p-4 text-center text-muted-foreground', className)}>
        <p>No historical indicator data available</p>
      </div>
    )
  }

  const chart = <MacroIndicatorHistoryChart series={series} />

  return (
    <div className={cn('flex min-w-0 flex-col gap-4', className)}>
      {framed ? (
        <Card className="min-w-0 overflow-hidden">
          <CardContent className="pt-6">{chart}</CardContent>
        </Card>
      ) : (
        chart
      )}

      {includeTable ? (
        <MacroIndicatorHistoryTable indicators={indicators} />
      ) : null}
    </div>
  )
}
