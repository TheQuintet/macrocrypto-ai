import {
  formatPrice,
  formatVolume,
  PRICE_PLACEHOLDER,
} from '@/components/dashboard/lib/priceFormat'
import { PriceDayStat } from '@/components/dashboard/price/PriceDayStat'

type PriceDayStatsProps = {
  high: number | null
  low: number | null
  volume: number | null
}

/**
 * The 24h session context under the price.
 * Wraps rather than truncates, so every value stays readable on a phone.
 */
export function PriceDayStats({ high, low, volume }: PriceDayStatsProps) {
  return (
    <dl className="flex min-w-0 flex-wrap items-baseline gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
      <PriceDayStat label="24h high" value={formatPriceOrPlaceholder(high)} />
      <PriceDayStat label="24h low" value={formatPriceOrPlaceholder(low)} />
      <PriceDayStat
        label="24h volume"
        value={volume == null ? PRICE_PLACEHOLDER : formatVolume(volume)}
      />
    </dl>
  )
}

function formatPriceOrPlaceholder(value: number | null) {
  return value == null ? PRICE_PLACEHOLDER : formatPrice(value)
}
