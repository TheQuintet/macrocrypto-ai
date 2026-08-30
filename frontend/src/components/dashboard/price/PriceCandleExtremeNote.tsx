import {
  formatSignedPercent,
  priceDirection,
  type PriceDirection,
} from '@/components/dashboard/lib/priceFormat'
import { cn } from '@/lib/utils'

const DIRECTION_MARK: Record<PriceDirection, string> = {
  up: '↑',
  down: '↓',
  flat: '→',
}

const DIRECTION_TONE: Record<PriceDirection, string> = {
  up: 'text-positive',
  down: 'text-negative',
  flat: 'text-muted-foreground',
}

type PriceCandleExtremeNoteProps = {
  changePercent: number
  reference: 'open' | 'close'
}

/** Signed move of high vs open, or low vs close. */
export function PriceCandleExtremeNote({
  changePercent,
  reference,
}: PriceCandleExtremeNoteProps) {
  const direction = priceDirection(changePercent)
  const text = `${DIRECTION_MARK[direction]} ${formatSignedPercent(changePercent)}`

  return (
    <span
      className={cn(DIRECTION_TONE[direction])}
      aria-label={`${text} from ${reference}`}
    >
      {text}
    </span>
  )
}
