import { Radio, RotateCw, WifiOff } from 'lucide-react'
import { formatUpdatedAt } from '@/components/dashboard/lib/priceFormat'
import { usePriceStream } from '@/hooks/usePriceStream'
import { cn } from '@/lib/utils'
import type { PriceStreamStatus as StreamStatus } from '@/types/priceStream'

const STATUS_LABEL: Record<StreamStatus, string> = {
  connecting: 'Connecting',
  connected: 'Live',
  disconnected: 'Reconnecting',
}

const STATUS_STYLE: Record<StreamStatus, string> = {
  connecting: 'text-muted-foreground',
  connected: 'text-positive',
  disconnected: 'text-negative',
}

const STATUS_ICON: Record<StreamStatus, typeof Radio> = {
  connecting: RotateCw,
  connected: Radio,
  disconnected: WifiOff,
}

/**
 * Owns the live price connection and reports it: status indicator plus the
 * time of the last frame received.
 */
export function PriceStreamStatus() {
  const { status, lastUpdatedAt } = usePriceStream()
  const StatusIcon = STATUS_ICON[status]

  return (
    <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1 text-xs">
      <span
        role="status"
        aria-label={`Price feed ${STATUS_LABEL[status]}`}
        className={cn(
          'inline-flex items-center gap-1 font-medium',
          STATUS_STYLE[status],
        )}
      >
        <StatusIcon className="size-3.5" aria-hidden="true" />
        {STATUS_LABEL[status]}
      </span>

      <span className="truncate tabular-nums text-muted-foreground">
        Updated {formatUpdatedAt(lastUpdatedAt)}
      </span>
    </div>
  )
}
