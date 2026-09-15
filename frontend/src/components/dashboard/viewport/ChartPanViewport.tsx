import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
  type WheelEvent as ReactWheelEvent,
} from 'react'
import type { ChartCandle } from '@/types/chart'
import { ChartPanPlotRow } from '@/components/dashboard/viewport/ChartPanPlotRow'
import { ChartYAxis } from '@/components/dashboard/viewport/ChartYAxis'
import { chartYAxisWidth, isChartCompact } from '@/components/dashboard/lib/chartTheme'
import { ChartZoomControls } from '@/components/dashboard/controls/ChartZoomControls'
import {
  DEFAULT_CHART_POINT_WIDTH,
  initialChartPointWidth,
  minChartPointWidth,
  shouldRenderAsLine,
  zoomChartPointWidth,
} from '@/components/dashboard/lib/chartZoom'
import { candleYDomain } from '@/components/dashboard/lib/chartCandle'

/** Fallback before ResizeObserver measures the plot area. */
const DEFAULT_CHART_HEIGHT = 224
const OVERSCAN_POINTS = 16

type PlotRenderArgs = {
  data: ChartCandle[]
  width: number
  height: number
  yDomain: [number, number]
  compact: boolean
  hideXAxis: boolean
  /** Candles are too thin to read at this density — draw a close line. */
  asLine: boolean
}

type ChartPanViewportProps = {
  data: ChartCandle[]
  showVisibleRange?: boolean
  secondaryYDomain?: (visible: ChartCandle[]) => [number, number]
  secondary?: (args: PlotRenderArgs) => ReactNode
  footer?: (args: { compact: boolean }) => ReactNode
  children: (args: PlotRenderArgs) => ReactNode
}

type DragState = {
  pointerId: number
  startX: number
  startOffsetX: number
}

/**
 * Wide chart strip with drag-to-pan and zoom in/out (point width).
 * Bars/lines slide via CSS transform instead of morphing values.
 * An optional secondary pane shares the same offset so dates stay aligned.
 */
export function ChartPanViewport({
  data,
  showVisibleRange = true,
  secondaryYDomain,
  secondary,
  footer,
  children,
}: ChartPanViewportProps) {
  const priceRowRef = useRef<HTMLDivElement>(null)
  const indicatorRowRef = useRef<HTMLDivElement>(null)
  const viewportRef = useRef<HTMLDivElement>(null)
  const [viewportWidth, setViewportWidth] = useState(0)
  const [priceHeight, setPriceHeight] = useState(DEFAULT_CHART_HEIGHT)
  const [indicatorHeight, setIndicatorHeight] = useState(DEFAULT_CHART_HEIGHT)
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
  const minPointWidth = minChartPointWidth(viewportWidth, data.length)
  // Re-fit when the range changes, and once more when the plot is first
  // measured — before that there is no width to divide between the candles.
  const nextSeriesKey = `${data.length}:${viewportWidth > 0 ? 'measured' : 'unmeasured'}`
  const hidePriceXAxis = Boolean(secondary)

  useEffect(() => {
    const viewportNode = viewportRef.current
    const priceRow = priceRowRef.current
    if (!viewportNode || !priceRow) {
      return
    }

    const syncSize = () => {
      setViewportWidth(viewportNode.clientWidth)
      setPriceHeight(priceRow.clientHeight || DEFAULT_CHART_HEIGHT)
      const indicatorRow = indicatorRowRef.current
      if (indicatorRow) {
        setIndicatorHeight(indicatorRow.clientHeight || DEFAULT_CHART_HEIGHT)
      }
    }

    syncSize()
    const observer = new ResizeObserver(syncSize)
    observer.observe(viewportNode)
    observer.observe(priceRow)
    const indicatorRow = indicatorRowRef.current
    if (indicatorRow) observer.observe(indicatorRow)
    return () => observer.disconnect()
  }, [hidePriceXAxis])

  if (seriesKey !== nextSeriesKey) {
    // Fit the selected range, rather than leaving the window at whatever
    // density the last range happened to use (#510).
    const fitted = initialChartPointWidth(viewportWidth, data.length)
    setSeriesKey(nextSeriesKey)
    setPointWidth(fitted)
    setOffsetX(Math.min(0, viewportWidth - data.length * fitted))
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

  const visibleEnd = Math.min(data.length, firstVisibleIndex + visibleCount)

  // Auto-scale to what is on screen, the way a trading chart does. Scaling to
  // the whole series would flatten the visible candles against the trend.
  // Before the viewport is measured there is no window yet, so fall back to
  // the whole series rather than collapsing onto an empty slice.
  const yDomain = useMemo(() => {
    const visible = data.slice(firstVisibleIndex, visibleEnd)
    return candleYDomain(visible.length > 0 ? visible : data)
  }, [data, firstVisibleIndex, visibleEnd])

  const indicatorYDomain = useMemo(() => {
    if (!secondaryYDomain) {
      return [0, 1] as [number, number]
    }
    const visible = data.slice(firstVisibleIndex, visibleEnd)
    return secondaryYDomain(visible.length > 0 ? visible : data)
  }, [data, firstVisibleIndex, visibleEnd, secondaryYDomain])

  // Formatted from `timeMs`, not reused from the candle's axis label: the
  // 1d/1w labels carry no year, so a fitted 1y range read "Sep 15 → Sep 15".
  const visibleFrom = formatVisibleBoundary(data[firstVisibleIndex])
  const visibleTo = formatVisibleBoundary(
    data[Math.min(data.length - 1, firstVisibleIndex + visibleCount - 1)],
  )

  function clampOffset(value: number, width = pointWidth) {
    const nextVirtualWidth = Math.max(viewportWidth, data.length * width)
    const nextMinOffsetX = Math.min(0, viewportWidth - nextVirtualWidth)
    return Math.min(0, Math.max(nextMinOffsetX, value))
  }

  function zoom(direction: 'in' | 'out') {
    const nextPointWidth = zoomChartPointWidth(
      pointWidth,
      direction,
      minPointWidth,
    )
    if (nextPointWidth === pointWidth || viewportWidth <= 0) {
      return
    }

    const centerIndex = (-clampedOffsetX + viewportWidth / 2) / pointWidth
    const nextOffset = viewportWidth / 2 - centerIndex * nextPointWidth

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

  const plotArgs = {
    data: renderData,
    width: renderWidth,
    compact,
    hideXAxis: hidePriceXAxis,
    asLine: shouldRenderAsLine(pointWidth),
  }
  const panHandlers = {
    renderWidth,
    stripOffsetX,
    canPan,
    isDragging,
    onPointerDown,
    onPointerMove,
    onPointerUp: endDrag,
    onPointerCancel: endDrag,
    onWheel,
  }

  return (
    <div className="flex w-full min-w-0 flex-col gap-5 sm:gap-6">
      <div className="flex flex-wrap items-center justify-between gap-2 pb-1">
        <ChartZoomControls
          pointWidth={pointWidth}
          minPointWidth={minPointWidth}
          onZoomIn={() => zoom('in')}
          onZoomOut={() => zoom('out')}
        />
        <p className="hidden text-xs text-muted-foreground sm:block">
          Ctrl/Cmd + wheel also zooms
        </p>
      </div>

      <ChartPanPlotRow
        yAxis={
          <ChartYAxis
            yDomain={yDomain}
            height={priceHeight}
            compact={compact}
            hideXAxis={hidePriceXAxis}
          />
        }
        yAxisWidth={yAxisWidth}
        heightClassName="flex h-56 w-full min-w-0 sm:h-72 md:h-[340px]"
        rowRef={priceRowRef}
        viewportRef={viewportRef}
        {...panHandlers}
      >
        {children({
          ...plotArgs,
          height: priceHeight,
          yDomain,
        })}
      </ChartPanPlotRow>

      {secondary ? (
        <ChartPanPlotRow
          yAxis={
            <ChartYAxis
              yDomain={indicatorYDomain}
              height={indicatorHeight}
              compact={compact}
              tickFormatter={(value) => value.toFixed(0)}
            />
          }
          yAxisWidth={yAxisWidth}
          heightClassName="flex h-56 w-full min-w-0 sm:h-72"
          rowRef={indicatorRowRef}
          {...panHandlers}
        >
          {secondary({
            ...plotArgs,
            height: indicatorHeight,
            yDomain: indicatorYDomain,
            hideXAxis: false,
          })}
        </ChartPanPlotRow>
      ) : null}

      {footer?.({ compact })}

      {showVisibleRange && visibleFrom && visibleTo ? (
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

/** Unambiguous end of the visible window, year included. */
function formatVisibleBoundary(candle: ChartCandle | undefined) {
  if (!candle) {
    return undefined
  }

  const date = new Date(candle.timeMs)

  if (Number.isNaN(date.getTime())) {
    return candle.time
  }

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  })
}
