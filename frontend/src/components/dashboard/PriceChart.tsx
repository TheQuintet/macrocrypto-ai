import { useMemo, useState } from 'react'
import { ChartIntervalSwitcher } from '@/components/dashboard/controls/ChartIntervalSwitcher'
import { PriceCandlestickChart } from '@/components/dashboard/price/PriceCandlestickChart'
import { PriceCandleReadout } from '@/components/dashboard/price/PriceCandleReadout'
import { CANDLE_INTERVAL_LABELS } from '@/components/dashboard/lib/chartInterval'
import { LINKED_CHART_SYNC_ID } from '@/components/dashboard/lib/chartTheme'
import { ChartPanViewport } from '@/components/dashboard/viewport/ChartPanViewport'
import { mapHistoryPointsToChartCandles } from '@/components/dashboard/lib/chartCandle'
import { MacroIndicatorHistoryChart } from '@/components/dashboard/indicators/MacroIndicatorHistoryChart'
import { TimeRangePicker } from '@/components/timeRange/TimeRangePicker'
import type { ChartCandle } from '@/types/chart'
import type { MacroIndicator } from '@/types/macroIndicators'
import { useBtcPriceHistoryQuery } from '@/hooks/useBtcPriceHistoryQuery'
import {
  asOfIndexedYDomain,
  attachAsOfIndicators,
  groupIndicatorsByName,
} from '@/lib/macroIndicatorHistory'
import { usePreferencesStore } from '@/stores/preferencesStore'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

type PriceChartProps = {
  framed?: boolean
  linkedIndicators?: MacroIndicator[]
  linkedIndicatorsLoading?: boolean
  linkedIndicatorsError?: Error | null
}

/**
 * Recharts baseline with production-like data flow:
 * API returns history already bucketed by interval; FE formats labels + renders.
 * Optional linkedIndicators share the candle X-axis (as-of prints, synced hover).
 */
export function PriceChart({
  framed = true,
  linkedIndicators,
  linkedIndicatorsLoading = false,
  linkedIndicatorsError = null,
}: PriceChartProps) {
  const timeRange = usePreferencesStore((state) => state.timeRange)
  const chartInterval = usePreferencesStore((state) => state.candleInterval)
  const isLinked = linkedIndicators !== undefined

  const historyQuery = useBtcPriceHistoryQuery({
    range: timeRange,
    interval: chartInterval,
  })

  const linkedSeries = useMemo(
    () => groupIndicatorsByName(linkedIndicators ?? []),
    [linkedIndicators],
  )

  const data = useMemo(() => {
    if (!historyQuery.data) {
      return []
    }

    const candles = mapHistoryPointsToChartCandles(
      historyQuery.data.points,
      historyQuery.data.interval,
    )

    if (!isLinked || linkedSeries.length === 0) {
      return candles
    }

    return attachAsOfIndicators(candles, linkedSeries)
  }, [historyQuery.data, isLinked, linkedSeries])

  const isInitialLoading = historyQuery.isPending && data.length === 0
  const isRefreshing = historyQuery.isFetching && data.length > 0
  const syncId = isLinked ? LINKED_CHART_SYNC_ID : undefined
  const seriesKey = `${data.length}:${data[0]?.timeMs ?? 0}:${data.at(-1)?.timeMs ?? 0}`
  const [inspectedCandle, setInspectedCandle] = useState<ChartCandle | null>(
    null,
  )
  const [inspectedSeriesKey, setInspectedSeriesKey] = useState(seriesKey)

  if (inspectedSeriesKey !== seriesKey) {
    setInspectedSeriesKey(seriesKey)
    setInspectedCandle(null)
  }

  const Root = framed ? 'section' : 'div'

  return (
    <Root
      className={cn(
        'flex w-full min-w-0 flex-col gap-3 p-3 text-left sm:p-4',
        framed &&
          'rounded-xl border border-border bg-card text-card-foreground ring-1 ring-foreground/10',
        !framed && 'pb-0 sm:pb-0',
      )}
    >
      <div className="min-w-0 space-y-2">
        <h2 className="text-sm font-medium">BTC price</h2>
        <div className="flex w-full min-w-0 flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <TimeRangePicker />
          <ChartIntervalSwitcher />
        </div>
        <p className="text-xs text-muted-foreground">
          Window{' '}
          <span className="font-medium text-foreground">{timeRange}</span>
          {' · '}
          <span className="font-medium text-foreground">
            {CANDLE_INTERVAL_LABELS[chartInterval]}
          </span>{' '}
          candles
          <span className="hidden sm:inline">
            {' — '}
            history loaded via simulated API (cached per range + interval).
          </span>
          {isRefreshing ? ' Refreshing…' : null}
        </p>
      </div>

      {historyQuery.isError ? (
        <p className="text-sm text-destructive">
          {historyQuery.error instanceof Error
            ? historyQuery.error.message
            : 'Failed to load price history'}
        </p>
      ) : null}

      {isInitialLoading ? (
        <p className="text-sm text-muted-foreground">Loading price history…</p>
      ) : (
        <div className="min-w-0 overflow-x-hidden">
          <ChartPanViewport
            data={data}
            showVisibleRange={framed}
            secondaryYDomain={isLinked ? asOfIndexedYDomain : undefined}
            footer={({ compact }) =>
              compact ? <PriceCandleReadout candle={inspectedCandle} /> : null
            }
            secondary={
              isLinked
                ? ({ data: panData, width, height, yDomain, compact }) => {
                    if (linkedIndicatorsLoading) {
                      return <Skeleton className="h-full w-full" />
                    }
                    if (linkedIndicatorsError) {
                      return (
                        <p className="p-3 text-sm text-destructive">
                          Failed to load historical indicator data
                        </p>
                      )
                    }
                    if (linkedSeries.length === 0) {
                      return (
                        <p className="p-3 text-sm text-muted-foreground">
                          No historical indicator data available
                        </p>
                      )
                    }
                    return (
                      <MacroIndicatorHistoryChart
                        series={linkedSeries}
                        candles={panData}
                        width={width}
                        height={height}
                        yDomain={yDomain}
                        compact={compact}
                        syncId={syncId}
                        overlayTooltip={!compact}
                        onInspect={setInspectedCandle}
                      />
                    )
                  }
                : undefined
            }
          >
            {({
              data: panData,
              width,
              height,
              yDomain,
              compact,
              hideXAxis,
            }) => (
              <PriceCandlestickChart
                data={panData}
                width={width}
                height={height}
                yDomain={yDomain}
                compact={compact}
                hideXAxis={hideXAxis}
                syncId={syncId}
                overlayTooltip={!compact}
                onInspect={setInspectedCandle}
              />
            )}
          </ChartPanViewport>
        </div>
      )}
    </Root>
  )
}
