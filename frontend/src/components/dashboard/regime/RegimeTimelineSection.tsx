import { useMemo, useState } from 'react'
import { RegimeDetailsDialog } from '@/components/dashboard/regime/RegimeDetailsDialog'
import { RegimeTimelineBand } from '@/components/dashboard/regime/RegimeTimelineBand'
import { RegimeTimelineZoom } from '@/components/dashboard/regime/RegimeTimelineZoom'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useRegimeHistoryQuery } from '@/hooks/useRegimeHistoryQuery'
import {
  buildTimelineSegments,
  MIN_TIMELINE_ZOOM,
  stepTimelineZoom,
} from '@/lib/regimeTimeline'

/** Historical macro regimes as one band — hover, click, and zoom. */
export function RegimeTimelineSection() {
  const { data, isPending, isError } = useRegimeHistoryQuery()
  const [zoom, setZoom] = useState<number>(MIN_TIMELINE_ZOOM)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const rows = useMemo(() => data?.rows ?? [], [data])
  // Held steady for the life of the component so the open regime's width does
  // not creep while the reader is looking at it.
  const [nowMs] = useState(() => Date.now())
  const segments = useMemo(
    () => buildTimelineSegments(rows, nowMs),
    [rows, nowMs],
  )
  const selected = rows.find((row) => row.id === selectedId) ?? null

  return (
    <section
      aria-label="Historical macro regimes"
      className="flex min-w-0 flex-col gap-3 overflow-hidden rounded-xl border border-border bg-card p-3 text-card-foreground sm:p-4"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 flex-col gap-1">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-sm font-medium">Regime timeline</h2>
            {data?.source === 'simulated' ? (
              <Badge variant="outline" className="text-[10px] font-normal">
                Simulated
              </Badge>
            ) : null}
          </div>
          <p className="text-xs text-muted-foreground">
            Every macro backdrop the service has classified, laid out by how
            long it ran. Hover for a summary, click for the detail.
          </p>
        </div>

        {segments.length > 0 ? (
          <RegimeTimelineZoom
            zoom={zoom}
            onZoomIn={() => setZoom((current) => stepTimelineZoom(current, 1))}
            onZoomOut={() =>
              setZoom((current) => stepTimelineZoom(current, -1))
            }
          />
        ) : null}
      </div>

      {renderBody(isPending, isError, segments, zoom, setSelectedId)}

      <RegimeDetailsDialog
        regime={selected}
        onClose={() => setSelectedId(null)}
      />
    </section>
  )
}

function renderBody(
  isPending: boolean,
  isError: boolean,
  segments: ReturnType<typeof buildTimelineSegments>,
  zoom: number,
  onSelect: (regimeId: number) => void,
) {
  if (isPending) {
    return <Skeleton className="h-14 w-full" />
  }

  if (isError) {
    return (
      <p role="alert" className="py-6 text-center text-xs text-negative">
        Regime history unavailable — retrying automatically
      </p>
    )
  }

  if (segments.length === 0) {
    return (
      <p className="py-6 text-center text-xs text-muted-foreground">
        No regimes have been classified yet — the timeline fills in as the
        service works through the indicator history.
      </p>
    )
  }

  return (
    <RegimeTimelineBand segments={segments} zoom={zoom} onSelect={onSelect} />
  )
}
