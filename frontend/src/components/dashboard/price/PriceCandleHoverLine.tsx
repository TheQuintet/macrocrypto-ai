/** Recharts clones the tooltip cursor with the hovered band's box. */
type PriceCandleHoverLineProps = {
  x?: number
  y?: number
  width?: number
  height?: number
}

/**
 * Vertical line marking the candle under the pointer.
 *
 * Recharts positions this from the hovered category band rather than by axis
 * value, so it lands on the right candle even when two buckets share a label.
 */
export function PriceCandleHoverLine({
  x = 0,
  y = 0,
  width = 0,
  height = 0,
}: PriceCandleHoverLineProps) {
  const centerX = x + width / 2

  return (
    <line
      data-slot="candle-hover-line"
      x1={centerX}
      x2={centerX}
      y1={y}
      y2={y + height}
      stroke="var(--muted-foreground)"
      strokeWidth={1}
      strokeDasharray="3 3"
    />
  )
}
