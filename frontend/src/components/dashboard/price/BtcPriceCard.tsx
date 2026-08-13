import { PriceDayStats } from '@/components/dashboard/price/PriceDayStats'
import { PriceStreamStatus } from '@/components/dashboard/price/PriceStreamStatus'
import { PriceValue } from '@/components/dashboard/price/PriceValue'
import { Badge } from '@/components/ui/badge'
import type { BtcPriceSnapshot } from '@/types/btcPrice'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useBtcPriceSnapshotQuery } from '@/hooks/useBtcPriceSnapshotQuery'
import { usePriceFlash } from '@/hooks/usePriceFlash'

/** Current BTC price in USD, shown as the dashboard's headline figure. */
export function BtcPriceCard() {
  const { data, isPending, isError } = useBtcPriceSnapshotQuery()
  const flashDirection = usePriceFlash(data?.currentPrice)

  const isUnavailable = isError || (!isPending && data?.currentPrice == null)

  return (
    <Card className="min-w-0">
      <CardHeader>
        <CardDescription className="flex flex-wrap items-center gap-2">
          BTC / USD
          {data?.source === 'simulated' ? (
            <Badge variant="outline" className="text-[10px] font-normal">
              Simulated
            </Badge>
          ) : null}
        </CardDescription>
        <CardTitle className="min-w-0">
          {isPending ? (
            <Skeleton className="h-8 w-36 sm:h-9 sm:w-44 lg:h-10 lg:w-52" />
          ) : (
            <PriceValue
              price={isUnavailable ? null : (data?.currentPrice ?? null)}
              flashDirection={flashDirection}
            />
          )}
        </CardTitle>
      </CardHeader>

      <CardContent className="flex flex-col gap-1.5">
        {renderFooter(isPending, isUnavailable, data)}
        <PriceStreamStatus />
      </CardContent>
    </Card>
  )
}

function renderFooter(
  isPending: boolean,
  isUnavailable: boolean,
  data: BtcPriceSnapshot | undefined,
) {
  if (isPending) {
    return <Skeleton className="h-3 w-48" />
  }

  if (isUnavailable) {
    return (
      <p role="alert" className="text-xs text-negative">
        Price unavailable — retrying automatically
      </p>
    )
  }

  return (
    <PriceDayStats
      high={data?.high24h ?? null}
      low={data?.low24h ?? null}
      volume={data?.volume24h ?? null}
    />
  )
}
