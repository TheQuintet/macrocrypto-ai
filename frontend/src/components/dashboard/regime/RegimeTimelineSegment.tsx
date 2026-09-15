import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { regimeDisplay } from '@/lib/regimeDisplay'
import { regimeSeriesColor } from '@/lib/regimeSeriesColor'
import { formatPercent, formatRegimeRange } from '@/lib/regimePerformance'
import { cn } from '@/lib/utils'
import type { RegimeTimelineSegment as Segment } from '@/types/regime'

type RegimeTimelineSegmentProps = {
  segment: Segment
  onSelect: (regimeId: number) => void
}

/** One regime on the band — hover for a summary, click for the full detail. */
export function RegimeTimelineSegment({
  segment,
  onSelect,
}: RegimeTimelineSegmentProps) {
  const { row } = segment
  const display = regimeDisplay(row.regimeType, 'neutral')
  const range = formatRegimeRange(row.startDate, row.endDate)

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          data-regime={row.regimeType}
          data-current={row.isCurrent ? 'true' : undefined}
          aria-label={`${display.label}, ${range}`}
          onClick={() => onSelect(row.id)}
          style={{
            left: `${segment.offsetPercent}%`,
            width: `${segment.widthPercent}%`,
            backgroundColor: regimeSeriesColor(row.regimeType),
          }}
          className={cn(
            'absolute inset-y-0 min-w-1 cursor-pointer border-r border-background/60',
            'transition-opacity hover:opacity-80',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60',
            // The regime the reader is in gets an outline rather than a
            // different colour, so its class is still readable.
            row.isCurrent && 'ring-2 ring-inset ring-foreground/70',
          )}
        >
          <span className="sr-only">{display.label}</span>
        </button>
      </TooltipTrigger>
      <TooltipContent className="flex max-w-[min(18rem,calc(100vw-2rem))] flex-col items-start gap-0.5">
        <span className="font-medium">
          {display.label}
          {row.isCurrent ? ' · current' : ''}
        </span>
        <span className="text-muted-foreground">{range}</span>
        {row.performance?.avgReturn != null ? (
          <span>BTC {formatPercent(row.performance.avgReturn)}</span>
        ) : null}
      </TooltipContent>
    </Tooltip>
  )
}
