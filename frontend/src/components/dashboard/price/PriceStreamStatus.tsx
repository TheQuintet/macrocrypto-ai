import { Radio, RefreshCw, RotateCw, WifiOff } from 'lucide-react';
import { formatUpdatedAt } from '@/components/dashboard/lib/priceFormat';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { useBtcPriceSnapshotQuery } from '@/hooks/useBtcPriceSnapshotQuery';
import { usePriceStream } from '@/hooks/usePriceStream';
import { cn } from '@/lib/utils';
import type { PriceStreamStatus as StreamStatus } from '@/types/priceStream';

const STATUS_LABEL: Record<StreamStatus, string> = {
  connecting: 'Connecting',
  connected: 'Live',
  disconnected: 'Disconnected',
  unavailable: 'Polling',
};

const STATUS_STYLE: Record<StreamStatus, string> = {
  connecting: 'text-warning',
  connected: 'text-positive',
  disconnected: 'text-negative',
  unavailable: 'text-positive',
};

const STATUS_ICON: Record<StreamStatus, typeof Radio> = {
  connecting: RotateCw,
  connected: Radio,
  disconnected: WifiOff,
  unavailable: RefreshCw,
};

const STATUS_DETAIL: Record<StreamStatus, string> = {
  connecting: 'Opening the price feed connection',
  connected: 'Receiving live price updates',
  disconnected: 'Price feed lost — retrying automatically',
  unavailable: 'No live stream configured — polling the price endpoint',
};

/**
 * Owns the live price connection and reports it: status indicator, the time
 * of the last frame received, and connection detail on hover.
 */
export function PriceStreamStatus() {
  const { status, reconnectAttempts } = usePriceStream();
  // The snapshot carries its own timestamp, and every transport writes the
  // same cache entry — so this works whether a stream or polling delivered it.
  const { data } = useBtcPriceSnapshotQuery();
  const lastUpdatedAt = data?.updatedAt ?? null;
  const StatusIcon = STATUS_ICON[status];
  const label = STATUS_LABEL[status];

  return (
    <div className='flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1 text-xs'>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            role='status'
            aria-label={`Price feed ${label}`}
            className={cn(
              'inline-flex cursor-default items-center gap-1 font-medium',
              STATUS_STYLE[status],
            )}
          >
            <StatusIcon className='size-3.5' aria-hidden='true' />
            {label}
          </span>
        </TooltipTrigger>

        <TooltipContent className='flex flex-col items-start gap-0.5'>
          <span className='font-medium'>{STATUS_DETAIL[status]}</span>
          <span className='tabular-nums'>
            Last update {formatUpdatedAt(lastUpdatedAt)}
          </span>
          {reconnectAttempts > 0 ? (
            <span className='tabular-nums'>
              Reconnect attempts {reconnectAttempts}
            </span>
          ) : null}
        </TooltipContent>
      </Tooltip>

      <span className='truncate tabular-nums text-muted-foreground'>
        Updated {formatUpdatedAt(lastUpdatedAt)}
      </span>
    </div>
  );
}
