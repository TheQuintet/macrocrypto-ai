import { useEffect, useRef, useState } from 'react'
import {
  flashDirectionFor,
  PRICE_FLASH_DURATION_MS,
  type PriceFlashDirection,
} from '@/components/dashboard/lib/priceFlash'

/**
 * Flash direction for the latest price move, cleared after the flash duration.
 *
 * The first observed price never flashes — there is nothing to compare against.
 * Comparison is always against the previous observed price, so a run of small
 * moves stays quiet even when it adds up to more than the threshold.
 */
export function usePriceFlash(price: number | null | undefined) {
  const [direction, setDirection] = useState<PriceFlashDirection>(null)
  const previousPriceRef = useRef<number | null>(null)

  useEffect(() => {
    if (price == null || !Number.isFinite(price)) {
      return
    }

    const previousPrice = previousPriceRef.current
    previousPriceRef.current = price

    if (previousPrice === null) {
      return
    }

    const nextDirection = flashDirectionFor(previousPrice, price)
    if (!nextDirection) {
      return
    }

    setDirection(nextDirection)
    const timer = setTimeout(() => setDirection(null), PRICE_FLASH_DURATION_MS)
    return () => clearTimeout(timer)
  }, [price])

  return direction
}
