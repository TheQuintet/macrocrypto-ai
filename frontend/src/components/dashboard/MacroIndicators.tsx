import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { MacroIndicatorCard } from '@/components/dashboard/indicators/MacroIndicatorCard'
import {
  MACRO_INDICATOR_SKELETON_COUNT,
  sortMacroIndicators,
} from '@/lib/macroIndicatorDisplay'
import { indicatorSeriesColor } from '@/lib/indicatorSeriesColor'
import { cn } from '@/lib/utils'
import type { MacroIndicator } from '@/types/macroIndicators'

interface MacroIndicatorsProps {
  indicators: MacroIndicator[]
  isLoading?: boolean
  error?: Error | null
  className?: string
}

export function MacroIndicators({
  indicators,
  isLoading = false,
  error = null,
  className,
}: MacroIndicatorsProps) {
  const isSimulated = indicators.some(
    (indicator) => indicator.dataSource === 'simulated',
  )
  const simulatedBadge = isSimulated ? (
    <Badge variant="outline" className="mb-2 w-fit text-[10px] font-normal">
      Simulated
    </Badge>
  ) : null
  if (isLoading) {
    return (
      <div className="flex min-w-0 flex-col">
        {simulatedBadge}
        <div
          className={cn(
            'grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 lg:grid-cols-3',
            className,
          )}
        >
          {Array.from({ length: MACRO_INDICATOR_SKELETON_COUNT }, (_, index) => (
            <Card
              key={`macro-indicator-skeleton-${index}`}
              className="min-w-0 overflow-hidden border-l-[3px]"
              style={{
                borderLeftColor: indicatorSeriesColor(
                  `skeleton-${index}`,
                ),
              }}
            >
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  <Skeleton className="h-4 w-20" />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Skeleton className="mb-2 h-8 w-24" />
                <Skeleton className="h-4 w-16" />
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
        {simulatedBadge}
        <p>Failed to load macroeconomic indicators</p>
        <p className="text-sm text-muted-foreground">{error.message}</p>
      </div>
    )
  }

  if (!indicators || indicators.length === 0) {
    return (
      <div className={cn('p-4 text-center text-muted-foreground', className)}>
        {simulatedBadge}
        <p>No macroeconomic data available</p>
      </div>
    )
  }

  return (
    <div className="flex min-w-0 flex-col">
      {simulatedBadge}
      <div
        className={cn(
          'grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 lg:grid-cols-3',
          className,
        )}
      >
        {sortMacroIndicators(indicators).map((indicator) => (
          <MacroIndicatorCard
            key={indicator.indicator_name}
            indicator={indicator}
          />
        ))}
      </div>
    </div>
  )
}
