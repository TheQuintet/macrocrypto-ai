import { ExampleQueryDemo } from '@/components/examples/ExampleQueryDemo'
import { PageHeader } from '@/components/layout/PageHeader'
import { TimeRangePicker } from '@/components/timeRange/TimeRangePicker'
import { BtcPriceCard } from '@/components/dashboard/price/BtcPriceCard'
import { PriceChangeCard } from '@/components/dashboard/price/PriceChangeCard'
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

const macroSnapshot = [
  { label: 'CPI (YoY)', hint: 'Inflation' },
  { label: 'Fed funds rate', hint: 'Policy' },
  { label: 'GDP', hint: 'Growth' },
]

export function DashboardPage() {
  const page = pageCopy.dashboard

  return (
    <div className="flex min-w-0 flex-col gap-4 sm:gap-6">
      <PageHeader title={page.title} description={page.body}>
        <TimeRangePicker />
      </PageHeader>

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 lg:grid-cols-3">
        <BtcPriceCard />

        <PriceChangeCard />

        <Card className="min-w-0 sm:col-span-2 lg:col-span-1">
          <CardHeader>
            <CardDescription>Macro regime</CardDescription>
            <CardTitle className="min-w-0 truncate text-base sm:text-lg lg:text-xl">
              <Skeleton className="h-5 w-28 sm:h-6 sm:w-36" />
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
    </div>
  )
}
