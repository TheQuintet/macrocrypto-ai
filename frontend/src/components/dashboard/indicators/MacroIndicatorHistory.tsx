import { useMemo } from 'react'
import { MacroIndicatorHistoryCard } from '@/components/dashboard/indicators/MacroIndicatorHistoryCard'
import { MacroIndicatorHistoryTable } from '@/components/dashboard/indicators/MacroIndicatorHistoryTable'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { MAIN_INDICATOR_NAMES } from '@/api/macroIndicators'
import { groupIndicatorsByName } from '@/lib/macroIndicatorHistory'
import { cn } from '@/lib/utils'
import type { MacroIndicator } from '@/types/macroIndicators'

type MacroIndicatorHistoryProps = {
  indicators: MacroIndicator[]
  isLoading?: boolean
  error?: Error | null
  className?: string
}

export function MacroIndicatorHistory({
  indicators,
  isLoading = false,
  error = null,
  className,
}: MacroIndicatorHistoryProps) {
  const series = useMemo(
    () => groupIndicatorsByName(indicators),
    [indicators],
  )

  if (isLoading) {
    return (
      <div className={cn('flex min-w-0 flex-col gap-4', className)}>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 lg:grid-cols-3">
          {MAIN_INDICATOR_NAMES.map((name) => (
            <Card key={name} className="min-w-0 overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  <Skeleton className="h-4 w-20" />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Skeleton className="h-36 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
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

  return (
    <div className={cn('flex min-w-0 flex-col gap-4', className)}>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 lg:grid-cols-3">
        {series.map((item) => (
          <MacroIndicatorHistoryCard key={item.name} series={item} />
        ))}
      </div>
      <MacroIndicatorHistoryTable indicators={indicators} />
    </div>
  )
}
