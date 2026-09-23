import { RegimeTimelineSegment } from '@/components/dashboard/regime/RegimeTimelineSegment'
import { timelineYearTicks } from '@/lib/regimeTimeline'
import type { RegimeTimelineSegment as Segment } from '@/types/regime'

type RegimeTimelineBandProps = {
  segments: Segment[]
  /** Multiple of the container width — above 1 the band scrolls sideways. */
  zoom: number
  onSelect: (regimeId: number) => void
}

/** The scrollable band itself: regimes in order, with year boundaries under. */
export function RegimeTimelineBand({
  segments,
  zoom,
  onSelect,
}: RegimeTimelineBandProps) {
  const ticks = timelineYearTicks(segments)

  return (
    <div className="min-w-0 overflow-x-auto pb-1">
      <div style={{ width: `${zoom * 100}%` }} className="min-w-full">
        <div className="relative h-10 overflow-hidden rounded-md border border-border bg-muted/40 sm:h-12">
          {segments.map((segment) => (
            <RegimeTimelineSegment
              key={segment.row.id}
              segment={segment}
              onSelect={onSelect}
            />
          ))}
        </div>

        <div className="relative mt-1 h-4">
          {ticks.map((tick) => (
            <span
              key={tick.label}
              style={{ left: `${tick.offsetPercent}%` }}
              className="absolute -translate-x-1/2 text-[10px] text-muted-foreground"
            >
              {tick.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
