/** Flash only on moves larger than this, in percent (issue #39). */
export const PRICE_FLASH_THRESHOLD_PERCENT = 1

/** How long the highlight stays on screen. */
export const PRICE_FLASH_DURATION_MS = 500

/** `null` means "no flash" — the move was not significant. */
export type PriceFlashDirection = 'up' | 'down' | null

export function percentChange(previous: number, next: number) {
  if (previous === 0) {
    return 0
  }

  return ((next - previous) / Math.abs(previous)) * 100
}

/**
 * Which way to flash for a price move, if at all.
 * Strictly greater than the threshold, so an exact 1% move stays quiet.
 */
export function flashDirectionFor(
  previous: number,
  next: number,
): PriceFlashDirection {
  const change = percentChange(previous, next)

  if (change > PRICE_FLASH_THRESHOLD_PERCENT) {
    return 'up'
  }

  if (change < -PRICE_FLASH_THRESHOLD_PERCENT) {
    return 'down'
  }

  return null
}

/** Animation utility for a flash direction (see `index.css`). */
export function priceFlashClass(direction: PriceFlashDirection) {
  if (direction === 'up') {
    return 'animate-price-flash-up'
  }

  return direction === 'down' ? 'animate-price-flash-down' : undefined
}
