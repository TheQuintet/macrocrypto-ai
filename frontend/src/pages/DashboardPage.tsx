import { ArrowUpRight } from 'lucide-react'
import { ExampleQueryDemo } from '@/components/examples/ExampleQueryDemo'
import { PageHeader } from '@/components/layout/PageHeader'
import { TimeRangePicker } from '@/components/timeRange/TimeRangePicker'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { pageCopy } from '@/constants/navigation'
import { PriceChart } from '@/components/dashboard/PriceChart'
import { MacroIndicators } from '@/components/dashboard/MacroIndicators'
import { useMacroIndicatorsQuery } from '@/hooks/useMacroIndicatorsQuery'

const macroSnapshot = [
  { label: 'CPI (YoY)', hint: 'Inflation' },
  { label: 'Fed funds rate', hint: 'Policy' },
  { label: 'GDP', hint: 'Growth' },
]

export function DashboardPage() {
  const page = pageCopy.dashboard
  const { data: indicators, isLoading, error } = useMacroIndicatorsQuery();

  return (
    <div className="flex min-w-0 flex-col gap-4 sm:gap-6">
      <PageHeader title={page.title} description={page.body}>
        <TimeRangePicker />
      </PageHeader>

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardDescription>BTC / USD</CardDescription>
            <CardTitle className="font-mono text-2xl sm:text-3xl">
              <Skeleton className="h-8 w-32 sm:h-9 sm:w-40" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xs text-muted-foreground">
              Awaiting live feed
            </span>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardDescription>24h change</CardDescription>
            <CardTitle className="flex items-center gap-2 font-mono text-2xl sm:text-3xl">
              <Skeleton className="h-8 w-24 sm:h-9 sm:w-28" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge
              variant="outline"
              className="gap-1 border-transparent bg-positive/10 text-positive"
            >
              <ArrowUpRight className="size-3" />
              <span className="font-mono">--.--%</span>
            </Badge>
          </CardContent>
        </Card>

        <Card className="sm:col-span-2 lg:col-span-1">
          <CardHeader>
            <CardDescription>Macro regime</CardDescription>
            <CardTitle className="text-lg sm:text-xl">
              <Skeleton className="h-6 w-36" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xs text-muted-foreground">
              AI-classified market context
            </span>
          </CardContent>
        </Card>
      </section>

      <section className="flex min-w-0 flex-col gap-3">
        <div className="flex flex-col gap-1">
          <h2 className="text-base font-medium">Price</h2>
          <p className="text-sm text-muted-foreground">
            Bitcoin spot with macro overlays
          </p>
        </div>
        <PriceChart />
      </section>

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-3 sm:gap-4">
        {macroSnapshot.map((item) => (
          <Card key={item.label}>
            <CardHeader>
              <CardDescription>{item.hint}</CardDescription>
              <CardTitle className="text-base">{item.label}</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              <Skeleton className="h-7 w-24" />
              <Skeleton className="h-3 w-16" />
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="flex min-w-0 flex-col gap-3">
        <div className="flex flex-col gap-1">
          <h2 className="text-base font-medium">Query patterns</h2>
          <p className="text-sm text-muted-foreground">
            Scaffold example for TanStack Query fetch + mutation flows.
          </p>
        </div>
        <ExampleQueryDemo />
      </section>

      <section className="flex min-w-0 flex-col gap-3">
         <div className="flex flex-col gap-1">
           <h2 className="text-base font-medium">Macroeconomic Indicators</h2>
           <p className="text-sm text-muted-foreground">
              Key economic indicators and their trends
           </p>
         </div>
         <MacroIndicators 
            indicators={indicators || []} 
            isLoading={isLoading}
            error={error}
          />
      </section>

    </div>
  )
}
