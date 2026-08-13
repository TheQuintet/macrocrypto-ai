import { Minus, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  MAX_CHART_POINT_WIDTH,
  MIN_CHART_POINT_WIDTH,
} from '@/components/dashboard/lib/chartZoom'

type ChartZoomControlsProps = {
  pointWidth: number
  onZoomIn: () => void
  onZoomOut: () => void
}

export function ChartZoomControls({
  pointWidth,
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
        disabled={pointWidth <= MIN_CHART_POINT_WIDTH}
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
        disabled={pointWidth >= MAX_CHART_POINT_WIDTH}
        onClick={onZoomIn}
      >
        <Plus />
      </Button>
    </div>
  )
}
