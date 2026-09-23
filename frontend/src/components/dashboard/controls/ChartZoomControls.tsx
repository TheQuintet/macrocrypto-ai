import { Minus, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  MAX_CHART_POINT_WIDTH,
  MIN_CHART_POINT_WIDTH,
} from '@/components/dashboard/lib/chartZoom'

type ChartZoomControlsProps = {
  /** Current zoom level, in whatever unit the caller zooms by. */
  value: number
  /** Bounds the buttons disable at; default to the pan chart's point widths. */
  min?: number
  max?: number
  onZoomIn: () => void
  onZoomOut: () => void
}

export function ChartZoomControls({
  value,
  min = MIN_CHART_POINT_WIDTH,
  max = MAX_CHART_POINT_WIDTH,
  onZoomIn,
  onZoomOut,
}: ChartZoomControlsProps) {
  return (
    <div
      className="flex items-center gap-2"
      role="group"
      aria-label="Chart zoom"
    >
      <Button
        type="button"
        size="icon-sm"
        variant="outline"
        aria-label="Zoom out"
        className="size-11 touch-manipulation sm:size-7"
        disabled={value <= min}
        onClick={onZoomOut}
      >
        <Minus />
      </Button>
      <Button
        type="button"
        size="icon-sm"
        variant="outline"
        aria-label="Zoom in"
        className="size-11 touch-manipulation sm:size-7"
        disabled={value >= max}
        onClick={onZoomIn}
      >
        <Plus />
      </Button>
    </div>
  )
}
