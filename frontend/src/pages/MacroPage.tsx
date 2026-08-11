import { PageHeader } from '@/components/layout/PageHeader'
import { TimeRangeBadge } from '@/components/timeRange/TimeRangeBadge'
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

const indicators = [
  {
    title: 'CPI',
    description: 'Consumer Price Index — headline & core inflation',
  },
  {
    title: 'Interest rates',
    description: 'Fed funds target & yield curve',
  },
  {
    title: 'GDP',
    description: 'Real output growth, quarter over quarter',
  },
]

export function MacroPage() {
  const page = pageCopy.macro

  return (
    <div className="flex min-w-0 flex-col gap-4 sm:gap-6">
      <PageHeader title={page.title} description={page.body}>
        <TimeRangeBadge />
      </PageHeader>

      <section className="grid grid-cols-1 gap-3 sm:gap-4 md:grid-cols-2 xl:grid-cols-3">
        {indicators.map((item) => (
          <Card key={item.title}>
            <CardHeader>
              <CardTitle className="text-base">{item.title}</CardTitle>
              <CardDescription>{item.description}</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <Skeleton className="h-8 w-28" />
              <Separator />
              <div className="flex flex-col gap-2">
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-4/5" />
                <Skeleton className="h-3 w-2/3" />
              </div>
            </CardContent>
          </Card>
        ))}
      </section>
    </div>
  )
}
