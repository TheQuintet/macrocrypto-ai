/** Direction of a change value — drives colour and arrow choice. */
export type PriceDirection = 'up' | 'down' | 'flat'

/** Placeholder shown wherever a value is missing. */
export const PRICE_PLACEHOLDER = '--'

/** `$64,213.50` — thousands separator, always 2 decimals. */
export function formatPrice(value: number) {
  return `$${value.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

/** `+$1,204.30` / `-$820.10` — absolute change with an explicit sign. */
export function formatSignedPrice(value: number) {
  return `${signOf(value)}${formatPrice(Math.abs(value))}`
}

/** `+1.88%` / `-0.42%`. */
export function formatSignedPercent(value: number) {
  return `${signOf(value)}${Math.abs(value).toFixed(2)}%`
}

export function priceDirection(value: number | null | undefined): PriceDirection {
  if (value == null || !Number.isFinite(value) || value === 0) {
    return 'flat'
  }

  return value > 0 ? 'up' : 'down'
}

function signOf(value: number) {
  if (value > 0) {
    return '+'
  }

  return value < 0 ? '-' : ''
}
