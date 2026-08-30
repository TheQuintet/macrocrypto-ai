import { percentChange } from '@/components/dashboard/lib/priceFormat'
import type { ChartCandle } from '@/types/chart'

/** Narrowest a candle body may render, so a doji stays visible. */
export const MIN_CANDLE_BODY_HEIGHT = 1

/** Widest a candle body may render, so sparse series stay readable. */
export const MAX_CANDLE_BODY_WIDTH = 18

export type CandleDirection = 'up' | 'down'

export type CandleLayout = {
  direction: CandleDirection
  /** Centre line of the slot — the wick's x. */
  centerX: number
  bodyX: number
  bodyWidth: number
  bodyY: number
  bodyHeight: number
  wickTopY: number
  wickBottomY: number
}

export function candleDirection(candle: ChartCandle): CandleDirection {
  return candle.close < candle.open ? 'down' : 'up'
}

/**
 * How far the wicks sit from the body edges the tooltip compares:
 * high vs open, low vs close.
 */
export function candleExtremePercents(candle: ChartCandle) {
  return {
    highFromOpen: percentChange(candle.open, candle.high),
    lowFromClose: percentChange(candle.close, candle.low),
  }
}

/**
 * Place one candle inside the slot Recharts assigns it.
 *
 * `slotY`/`slotHeight` come from a floating bar spanning [low, high], so the
 * high/low pixels are known and open/close interpolate between them.
 */
export function candleLayout(
  candle: ChartCandle,
  slotX: number,
  slotY: number,
  slotWidth: number,
  slotHeight: number,
): CandleLayout {
  const bodyWidth = Math.max(1, Math.min(slotWidth * 0.7, MAX_CANDLE_BODY_WIDTH))
  const centerX = slotX + slotWidth / 2
  const priceToY = makePriceToY(candle, slotY, slotHeight)

  const bodyTop = priceToY(Math.max(candle.open, candle.close))
  const bodyBottom = priceToY(Math.min(candle.open, candle.close))

  return {
    direction: candleDirection(candle),
    centerX,
    bodyX: centerX - bodyWidth / 2,
    bodyWidth,
    bodyY: bodyTop,
    bodyHeight: Math.max(MIN_CANDLE_BODY_HEIGHT, bodyBottom - bodyTop),
    wickTopY: slotY,
    wickBottomY: slotY + slotHeight,
  }
}

/**
 * Map a price onto the slot's pixel span. A flat bucket (high === low) has no
 * span to interpolate across, so everything collapses onto the slot top.
 */
function makePriceToY(candle: ChartCandle, slotY: number, slotHeight: number) {
  const priceSpan = candle.high - candle.low

  return (price: number) => {
    if (priceSpan <= 0) {
      return slotY
    }

    return slotY + ((candle.high - price) / priceSpan) * slotHeight
  }
}
