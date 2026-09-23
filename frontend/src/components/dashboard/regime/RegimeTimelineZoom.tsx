import { Minus, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  MAX_TIMELINE_ZOOM,
  MIN_TIMELINE_ZOOM,
} from '@/lib/regimeTimeline'

type RegimeTimelineZoomProps = {
  zoom: number
  onZoomIn: () => void
  onZoomOut: () => void
}

/** Widen the band to separate short regimes, or fit the whole span again. */
export function RegimeTimelineZoom({
  zoom,
  onZoomIn,
  onZoomOut,
}: RegimeTimelineZoomProps) {
  return (
    <div className="flex items-center gap-1">
      <Button
        type="button"
        variant="outline"
        size="icon"
        className="size-8"
        aria-label="Zoom out of the regime timeline"
        disabled={zoom <= MIN_TIMELINE_ZOOM}
        onClick={onZoomOut}
      >
        <Minus className="size-3.5" />
      </Button>
      <span
        aria-live="polite"
        className="min-w-9 text-center text-xs tabular-nums text-muted-foreground"
      >
        {zoom}x
      </span>
      <Button
        type="button"
        variant="outline"
        size="icon"
        className="size-8"
        aria-label="Zoom into the regime timeline"
        disabled={zoom >= MAX_TIMELINE_ZOOM}
        onClick={onZoomIn}
      >
        <Plus className="size-3.5" />
      </Button>
    </div>
  )
}
