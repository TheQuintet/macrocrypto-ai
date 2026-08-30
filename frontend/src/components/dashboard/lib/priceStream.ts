import { mapBtcPriceSnapshot } from '@/api/btcPrice/btcPrice'
import type { BtcPriceSnapshot, PriceSource } from '@/types/btcPrice'

/** First retry waits this long; each further attempt doubles it. */
export const RECONNECT_BASE_DELAY_MS = 1_000

/** Ceiling so a long outage keeps retrying at a steady, sane cadence. */
export const RECONNECT_MAX_DELAY_MS = 16_000

/** Exponential backoff for reconnect attempt `attempt` (1-based). */
export function reconnectDelayMs(attempt: number) {
  const exponential = RECONNECT_BASE_DELAY_MS * 2 ** Math.max(0, attempt - 1)

  return Math.min(exponential, RECONNECT_MAX_DELAY_MS)
}

/**
 * Parse a price frame off the wire.
 * Returns `null` for anything unreadable — a malformed frame must not take
 * the connection or the display down with it. Absent fields become `null`,
 * matching how the service reports values it does not have yet.
 */
export function parsePriceStreamMessage(
  data: string,
  source: PriceSource = 'live',
): BtcPriceSnapshot | null {
  let parsed: unknown

  try {
    parsed = JSON.parse(data)
  } catch {
    return null
  }

  if (typeof parsed !== 'object' || parsed === null) {
    return null
  }

  const frame = parsed as Record<string, unknown>
  if (!('current_price' in frame)) {
    return null
  }

  return mapBtcPriceSnapshot({
    current_price: numberOrNull(frame.current_price),
    change_24h: numberOrNull(frame.change_24h),
    change_24h_percent: numberOrNull(frame.change_24h_percent),
    high_24h: numberOrNull(frame.high_24h),
    low_24h: numberOrNull(frame.low_24h),
    volume_24h: numberOrNull(frame.volume_24h),
    change_7d: numberOrNull(frame.change_7d),
    change_7d_percent: numberOrNull(frame.change_7d_percent),
    updated_at: stringOrNull(frame.updated_at),
  }, source)
}

function numberOrNull(value: unknown) {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function stringOrNull(value: unknown) {
  return typeof value === 'string' ? value : null
}
