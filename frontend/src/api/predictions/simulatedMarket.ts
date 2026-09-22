/**
 * One deterministic price curve behind every simulated forecast figure.
 *
 * History candles sample it in the past and the forecast mean continues it
 * into the future, so the two halves of the chart tell one story. Generating
 * them from separate functions let the projection climb out of a window that
 * had been falling all day, which is not something a model would ever say.
 */

export const HOUR_MS = 60 * 60 * 1000

const BASE_PRICE = 64_000

/**
 * Two oscillations rather than a trend: a slow swing that sets the mood of a
 * window, and a faster one that turns within it. A linear drift would make
 * every forecast point the same direction forever.
 */
const SLOW_PERIOD_HOURS = 91
const SLOW_AMPLITUDE = 0.035
const FAST_PERIOD_HOURS = 23
const FAST_AMPLITUDE = 0.011

/** The underlying price at a moment — same input, same output, always. */
export function marketPriceAt(ms: number) {
  const hours = ms / HOUR_MS
  const slow = Math.sin((hours / SLOW_PERIOD_HOURS) * Math.PI * 2)
  const fast = Math.sin((hours / FAST_PERIOD_HOURS) * Math.PI * 2)

  return BASE_PRICE * (1 + slow * SLOW_AMPLITUDE + fast * FAST_AMPLITUDE)
}

/**
 * Where the curve is heading over the next `horizonMs`, as a fraction of the
 * current price. The forecast's slope, taken from the same curve the candles
 * were drawn from.
 */
export function marketDriftRatio(nowMs: number, horizonMs: number) {
  const current = marketPriceAt(nowMs)

  return (marketPriceAt(nowMs + horizonMs) - current) / current
}
