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

/** Percent change from `from` to `to`. Flat when the base cannot be used. */
export function percentChange(from: number, to: number): number {
  if (from === 0 || !Number.isFinite(from) || !Number.isFinite(to)) {
    return 0
  }
  return ((to - from) / from) * 100
}

/** `24,180.42 BTC` — 24h traded volume in the base asset. */
export function formatVolume(value: number) {
  return `${value.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} BTC`
}

/**
 * Wall-clock time of the last update, e.g. `14:32:05`.
 * Rendered in the reader's own timezone — this is a "how fresh is this"
 * signal, not a timestamp anyone reconciles across zones.
 */
export function formatUpdatedAt(isoTimestamp: string | null | undefined) {
  if (!isoTimestamp) {
    return PRICE_PLACEHOLDER
  }

  const parsed = new Date(isoTimestamp)
  if (Number.isNaN(parsed.getTime())) {
    return PRICE_PLACEHOLDER
  }

  return parsed.toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
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
