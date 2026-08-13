import {
  priceFlashClass,
  type PriceFlashDirection,
} from '@/components/dashboard/lib/priceFlash'
import {
  formatPrice,
  PRICE_PLACEHOLDER,
} from '@/components/dashboard/lib/priceFormat'
import { cn } from '@/lib/utils'

type PriceValueProps = {
  price: number | null
  flashDirection?: PriceFlashDirection
}

/** The current price itself — large, bold, and briefly tinted on big moves. */
export function PriceValue({
  price,
  flashDirection = null,
}: PriceValueProps) {
  return (
    <span
      data-flash={flashDirection ?? 'none'}
      className={cn(
        '-mx-1 inline-flex min-w-0 rounded-md px-1 font-mono text-2xl font-bold tabular-nums sm:text-3xl lg:text-4xl',
        priceFlashClass(flashDirection),
      )}
    >
      {price == null ? PRICE_PLACEHOLDER : formatPrice(price)}
    </span>
  )
}
