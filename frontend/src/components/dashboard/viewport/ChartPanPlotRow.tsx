import type {
  PointerEvent as ReactPointerEvent,
  ReactNode,
  Ref,
  WheelEvent as ReactWheelEvent,
} from 'react'
import { cn } from '@/lib/utils'

type ChartPanPlotRowProps = {
  yAxis: ReactNode
  yAxisWidth: number
  heightClassName: string
  rowRef?: Ref<HTMLDivElement>
  viewportRef?: Ref<HTMLDivElement>
  renderWidth: number
  stripOffsetX: number
  canPan: boolean
  isDragging: boolean
  onPointerDown: (event: ReactPointerEvent<HTMLDivElement>) => void
  onPointerMove: (event: ReactPointerEvent<HTMLDivElement>) => void
  onPointerUp: (event: ReactPointerEvent<HTMLDivElement>) => void
  onPointerCancel: (event: ReactPointerEvent<HTMLDivElement>) => void
  onWheel: (event: ReactWheelEvent<HTMLDivElement>) => void
  children: ReactNode
}

/** One Y-axis + panning strip; stacked rows share offset and point width. */
export function ChartPanPlotRow({
  yAxis,
  yAxisWidth,
  heightClassName,
  rowRef,
  viewportRef,
  renderWidth,
  stripOffsetX,
  canPan,
  isDragging,
  onPointerDown,
  onPointerMove,
  onPointerUp,
  onPointerCancel,
  onWheel,
  children,
}: ChartPanPlotRowProps) {
  return (
    <div ref={rowRef} className={heightClassName}>
      <div className="shrink-0 bg-background" style={{ width: yAxisWidth }}>
        {yAxis}
      </div>
      <div
        ref={viewportRef}
        className={cn(
          'h-full min-w-0 flex-1 overflow-hidden touch-pan-y select-none',
          canPan && (isDragging ? 'cursor-grabbing' : 'cursor-grab'),
        )}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerCancel}
        onWheel={onWheel}
        role="presentation"
      >
        <div
          className="h-full will-change-transform"
          style={{
            width: renderWidth,
            transform: `translate3d(${stripOffsetX}px, 0, 0)`,
          }}
        >
          {children}
        </div>
      </div>
    </div>
  )
}
