import { PriceChangeStat } from '@/components/dashboard/price/PriceChangeStat'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { useBtcPriceSnapshotQuery } from '@/hooks/useBtcPriceSnapshotQuery'

/** 24h and 7d price changes, shown alongside the current price. */
export function PriceChangeCard() {
  const { data, isPending, isError } = useBtcPriceSnapshotQuery()

  return (
    <Card className="min-w-0">
      <CardHeader>
        <CardDescription>Price change</CardDescription>
      </CardHeader>

      <CardContent className="flex flex-col gap-2">
        {isPending ? (
          <>
            <Skeleton className="h-8 w-full" />
            <Separator />
            <Skeleton className="h-8 w-full" />
          </>
        ) : (
          <>
            <PriceChangeStat
              changeWindow="24h"
              changeAbsolute={isError ? null : (data?.change24h ?? null)}
              changePercent={isError ? null : (data?.change24hPercent ?? null)}
            />
            <Separator />
            <PriceChangeStat
              changeWindow="7d"
              changeAbsolute={isError ? null : (data?.change7d ?? null)}
              changePercent={isError ? null : (data?.change7dPercent ?? null)}
            />
          </>
        )}
      </CardContent>
    </Card>
  )
}
