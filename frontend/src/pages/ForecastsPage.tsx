import { ChartPlaceholder } from '@/components/charts/ChartPlaceholder'
import { PageIntro } from '@/components/layout/PageIntro'
import { TimeRangeBadge } from '@/components/timeRange/TimeRangeBadge'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { pageCopy } from '@/constants/navigation'

export function ForecastsPage() {
  const page = pageCopy.forecasts

  return (
    <div className="flex min-w-0 flex-col gap-4 sm:gap-6">
      <PageIntro description={page.body}>
        <TimeRangeBadge />
      </PageIntro>

      <div className="grid grid-cols-1 gap-3 sm:gap-4 lg:grid-cols-3">
        <Card className="min-w-0 lg:col-span-2">
          <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex min-w-0 flex-col gap-1">
              <CardTitle>24h prediction</CardTitle>
              <CardDescription>
                Projected price path with uncertainty band
              </CardDescription>
            </div>
            <Badge variant="secondary" className="w-fit font-mono">
              Next 24h
            </Badge>
          </CardHeader>
          <CardContent className="min-w-0">
            <ChartPlaceholder
              className="h-56 sm:h-[280px] md:h-[340px]"
              label="Forecast"
            />
          </CardContent>
        </Card>

        <Card className="min-w-0">
          <CardHeader>
            <CardTitle className="text-base">Confidence</CardTitle>
            <CardDescription>Model certainty for this window</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-5">
            <div className="flex flex-col gap-2">
              <Skeleton className="h-10 w-24" />
              <Skeleton className="h-2 w-full rounded-full" />
            </div>
            <Separator />
            <div className="flex flex-col gap-3">
              {['Direction', 'Expected range', 'Key driver'].map((label) => (
                <div
                  key={label}
                  className="flex items-center justify-between gap-4"
                >
                  <span className="text-sm text-muted-foreground">{label}</span>
                  <Skeleton className="h-4 w-16 sm:w-20" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
