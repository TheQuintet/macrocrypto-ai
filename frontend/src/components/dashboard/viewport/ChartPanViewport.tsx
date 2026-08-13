import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
  type WheelEvent as ReactWheelEvent,
} from 'react'
import type { ChartPoint } from '@/types/chart'
import { ChartYAxis } from '@/components/dashboard/viewport/ChartYAxis'
import {
  chartYAxisWidth,
  isChartCompact,
} from '@/components/dashboard/lib/chartTheme'
import { ChartZoomControls } from '@/components/dashboard/controls/ChartZoomControls'
import {
  DEFAULT_CHART_POINT_WIDTH,
  zoomChartPointWidth,
} from '@/components/dashboard/lib/chartZoom'
import { cn } from '@/lib/utils'

/** Fallback before ResizeObserver measures the plot area. */
const DEFAULT_CHART_HEIGHT = 224
const OVERSCAN_POINTS = 16

type ChartPanViewportProps = {
  data: ChartPoint[]
  children: (args: {
    data: ChartPoint[]
    width: number
    height: number
    yDomain: [number, number]
    compact: boolean
  }) => ReactNode
}

type DragState = {
  pointerId: number
  startX: number
  startOffsetX: number
}

/**
 * Wide chart strip with drag-to-pan and zoom in/out (point width).
 * Bars/lines slide via CSS transform instead of morphing values.
 */
export function ChartPanViewport({
  data,
  children,
}: ChartPanViewportProps) {
  const chartRowRef = useRef<HTMLDivElement>(null)
  const viewportRef = useRef<HTMLDivElement>(null)
  const [viewportWidth, setViewportWidth] = useState(0)
  const [chartHeight, setChartHeight] = useState(DEFAULT_CHART_HEIGHT)
  const [offsetX, setOffsetX] = useState(0)
  const [pointWidth, setPointWidth] = useState(DEFAULT_CHART_POINT_WIDTH)
  const [seriesKey, setSeriesKey] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const dragRef = useRef<DragState | null>(null)

  const compact = isChartCompact(viewportWidth)
  const yAxisWidth = chartYAxisWidth(compact)
  const virtualWidth = Math.max(viewportWidth, data.length * pointWidth)
  const minOffsetX = Math.min(0, viewportWidth - virtualWidth)
  const canPan = virtualWidth > viewportWidth + 1
  const nextSeriesKey = `${data.length}`

  const yDomain = useMemo((): [number, number] => {
    if (data.length === 0) {
      return [0, 1]
    }

    let min = data[0].price
    let max = data[0].price
    for (const point of data) {
      min = Math.min(min, point.price)
      max = Math.max(max, point.price)
    }

    return [min - 200, max + 200]
  }, [data])

  useEffect(() => {
    const viewportNode = viewportRef.current
    const rowNode = chartRowRef.current
    if (!viewportNode || !rowNode) {
      return
    }

    const syncSize = () => {
      setViewportWidth(viewportNode.clientWidth)
      setChartHeight(rowNode.clientHeight || DEFAULT_CHART_HEIGHT)
    }

    syncSize()
    const observer = new ResizeObserver(syncSize)
    observer.observe(viewportNode)
    observer.observe(rowNode)
    return () => observer.disconnect()
  }, [])

  if (seriesKey !== nextSeriesKey) {
    setSeriesKey(nextSeriesKey)
    setOffsetX(minOffsetX)
  }

  const clampedOffsetX = Math.min(0, Math.max(minOffsetX, offsetX))

  const firstVisibleIndex = Math.max(
    0,
    Math.floor(-clampedOffsetX / pointWidth),
  )
  const visibleCount = Math.max(
    1,
    Math.ceil((viewportWidth || pointWidth) / pointWidth),
  )
  const renderStart = Math.max(0, firstVisibleIndex - OVERSCAN_POINTS)
  const renderEnd = Math.min(
    data.length,
    firstVisibleIndex + visibleCount + OVERSCAN_POINTS,
  )
  const renderData = data.slice(renderStart, renderEnd)
  const renderWidth = Math.max(viewportWidth, renderData.length * pointWidth)
  const stripOffsetX = clampedOffsetX + renderStart * pointWidth

  const visibleFrom = data[firstVisibleIndex]?.time
  const visibleTo =
    data[Math.min(data.length - 1, firstVisibleIndex + visibleCount - 1)]?.time

  function clampOffset(value: number, width = pointWidth) {
    const nextVirtualWidth = Math.max(viewportWidth, data.length * width)
    const nextMinOffsetX = Math.min(0, viewportWidth - nextVirtualWidth)
    return Math.min(0, Math.max(nextMinOffsetX, value))
  }

  function zoom(direction: 'in' | 'out') {
    const nextPointWidth = zoomChartPointWidth(pointWidth, direction)
    if (nextPointWidth === pointWidth || viewportWidth <= 0) {
      return
    }

    const centerIndex =
      (-clampedOffsetX + viewportWidth / 2) / pointWidth
    const nextOffset =
      viewportWidth / 2 - centerIndex * nextPointWidth

    setPointWidth(nextPointWidth)
    setOffsetX(clampOffset(nextOffset, nextPointWidth))
  }

  function onPointerDown(event: ReactPointerEvent<HTMLDivElement>) {
    if (!canPan || event.button !== 0) {
      return
    }

    dragRef.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startOffsetX: clampedOffsetX,
    }
    setIsDragging(true)
    event.currentTarget.setPointerCapture(event.pointerId)
  }

  function onPointerMove(event: ReactPointerEvent<HTMLDivElement>) {
    const drag = dragRef.current
    if (!drag || drag.pointerId !== event.pointerId) {
      return
    }

    const nextOffset = drag.startOffsetX + (event.clientX - drag.startX)
    setOffsetX(clampOffset(nextOffset))
  }

  function endDrag(event: ReactPointerEvent<HTMLDivElement>) {
    const drag = dragRef.current
    if (!drag || drag.pointerId !== event.pointerId) {
      return
    }

    dragRef.current = null
    setIsDragging(false)
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId)
    }
  }

  function onWheel(event: ReactWheelEvent<HTMLDivElement>) {
    if (event.ctrlKey || event.metaKey) {
      event.preventDefault()
      zoom(event.deltaY < 0 ? 'in' : 'out')
      return
    }

    if (!canPan) {
      return
    }

    const delta =
      Math.abs(event.deltaX) > Math.abs(event.deltaY)
        ? event.deltaX
        : event.deltaY
    if (delta === 0) {
      return
    }

    event.preventDefault()
    setOffsetX(clampOffset(clampedOffsetX - delta))
  }

  return (
    <div className="flex w-full min-w-0 flex-col gap-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <ChartZoomControls
          pointWidth={pointWidth}
          onZoomIn={() => zoom('in')}
          onZoomOut={() => zoom('out')}
        />
        <p className="hidden text-xs text-muted-foreground sm:block">
          Ctrl/Cmd + wheel also zooms
        </p>
      </div>

      <div
        ref={chartRowRef}
        className="flex h-56 w-full min-w-0 sm:h-72 md:h-[340px]"
      >
        <div
          className="shrink-0 bg-background"
          style={{ width: yAxisWidth }}
        >
          <ChartYAxis
            yDomain={yDomain}
            height={chartHeight}
            compact={compact}
          />
        </div>

        <div
          ref={viewportRef}
          className={cn(
            'h-full min-w-0 flex-1 overflow-hidden touch-pan-y select-none',
            canPan && (isDragging ? 'cursor-grabbing' : 'cursor-grab'),
          )}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={endDrag}
          onPointerCancel={endDrag}
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
            {children({
              data: renderData,
              width: renderWidth,
              height: chartHeight,
              yDomain,
              compact,
            })}
          </div>
        </div>
      </div>

      {visibleFrom && visibleTo ? (
        <p className="text-xs text-muted-foreground">
          Showing <span className="font-medium text-foreground">{visibleFrom}</span>
          {' → '}
          <span className="font-medium text-foreground">{visibleTo}</span>
          <span className="hidden sm:inline">
            {canPan ? ' · drag to slide · zoom to change density' : null}
          </span>
          <span className="sm:hidden">
            {canPan ? ' · drag or zoom' : null}
          </span>
        </p>
      ) : null}
    </div>
  )
}
