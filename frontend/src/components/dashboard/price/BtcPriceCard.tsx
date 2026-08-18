import { PriceValue } from '@/components/dashboard/price/PriceValue'
import {
  formatPrice,
  PRICE_PLACEHOLDER,
} from '@/components/dashboard/lib/priceFormat'
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
        <CardDescription>BTC / USD</CardDescription>
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

      <CardContent>{renderFooter(isPending, isUnavailable, data)}</CardContent>
    </Card>
  )
}

function renderFooter(
  isPending: boolean,
  isUnavailable: boolean,
  data: { high24h: number | null; low24h: number | null } | undefined,
) {
  if (isPending) {
    return <Skeleton className="h-3 w-40" />
  }

  if (isUnavailable) {
    return (
      <p role="alert" className="text-xs text-negative">
        Price unavailable — retrying automatically
      </p>
    )
  }

  return (
    <p className="truncate text-xs tabular-nums text-muted-foreground">
      24h high {formatOrPlaceholder(data?.high24h)} · low{' '}
      {formatOrPlaceholder(data?.low24h)}
    </p>
  )
}

function formatOrPlaceholder(value: number | null | undefined) {
  return value == null ? PRICE_PLACEHOLDER : formatPrice(value)
}
