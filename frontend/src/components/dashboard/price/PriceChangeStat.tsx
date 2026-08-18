import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'
import {
  formatSignedPercent,
  formatSignedPrice,
  PRICE_PLACEHOLDER,
  priceDirection,
  type PriceDirection,
} from '@/components/dashboard/lib/priceFormat'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { PriceChangeWindow } from '@/types/btcPrice'

type PriceChangeStatProps = {
  changeWindow: PriceChangeWindow
  changeAbsolute: number | null
  changePercent: number | null
}

const WINDOW_LABEL: Record<PriceChangeWindow, string> = {
  '24h': '24h change',
  '7d': '7d change',
}

const DIRECTION_STYLE: Record<PriceDirection, string> = {
  up: 'bg-positive/10 text-positive',
  down: 'bg-negative/10 text-negative',
  flat: 'bg-muted text-muted-foreground',
}

const DIRECTION_ICON: Record<PriceDirection, typeof Minus> = {
  up: ArrowUpRight,
  down: ArrowDownRight,
  flat: Minus,
}

/** One change window: percentage badge plus the absolute move. */
export function PriceChangeStat({
  changeWindow,
  changeAbsolute,
  changePercent,
}: PriceChangeStatProps) {
  const label = WINDOW_LABEL[changeWindow]
  const direction = priceDirection(changePercent)
  const DirectionIcon = DIRECTION_ICON[direction]

  return (
    <div
      role="group"
      aria-label={label}
      className="flex min-w-0 flex-wrap items-center justify-between gap-x-3 gap-y-1"
    >
      <span className="text-xs text-muted-foreground">{label}</span>

      <div className="flex min-w-0 items-center gap-2">
        <Badge
          variant="outline"
          className={cn(
            'min-h-8 gap-1 border-transparent',
            DIRECTION_STYLE[direction],
          )}
        >
          <DirectionIcon className="size-3.5" aria-hidden="true" />
          <span className="font-mono tabular-nums">
            {changePercent == null
              ? PRICE_PLACEHOLDER
              : formatSignedPercent(changePercent)}
          </span>
        </Badge>

        <span className="truncate font-mono text-sm tabular-nums text-muted-foreground">
          {changeAbsolute == null
            ? PRICE_PLACEHOLDER
            : formatSignedPrice(changeAbsolute)}
        </span>
      </div>
    </div>
  )
}
