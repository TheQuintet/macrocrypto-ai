import { useMemo, useState } from 'react'
import { PriceCandlestickChart } from '@/components/dashboard/price/PriceCandlestickChart'
import { ChartIntervalSwitcher } from '@/components/dashboard/controls/ChartIntervalSwitcher'
import {
  DEFAULT_CHART_INTERVAL,
} from '@/components/dashboard/lib/chartInterval'
import { ChartPanViewport } from '@/components/dashboard/viewport/ChartPanViewport'
import { mapHistoryPointsToChartCandles } from '@/components/dashboard/lib/chartCandle'
import { ChartTypeSwitcher } from '@/components/dashboard/controls/ChartTypeSwitcher'
import type { ChartInterval, ChartType } from '@/types/chart'
import { PriceLineChart } from '@/components/dashboard/price/PriceLineChart'
import { useBtcPriceHistoryQuery } from '@/hooks/useBtcPriceHistoryQuery'
import { usePreferencesStore } from '@/stores/preferencesStore'

/**
 * Recharts baseline with production-like data flow:
 * API returns history already bucketed by interval; FE formats labels + renders.
 */
export function PriceChart() {
  const timeRange = usePreferencesStore((state) => state.timeRange)
  const [chartType, setChartType] = useState<ChartType>('line')
  const [chartInterval, setChartInterval] = useState<ChartInterval>(
    DEFAULT_CHART_INTERVAL,
  )

  const historyQuery = useBtcPriceHistoryQuery({
    range: timeRange,
    interval: chartInterval,
  })

  const data = useMemo(() => {
    if (!historyQuery.data) {
      return []
    }

    return mapHistoryPointsToChartCandles(
      historyQuery.data.points,
      historyQuery.data.interval,
    )
  }, [historyQuery.data])

  const isInitialLoading = historyQuery.isPending && data.length === 0
  const isRefreshing = historyQuery.isFetching && data.length > 0

  return (
    <section className="flex w-full min-w-0 flex-col gap-3 rounded-xl border border-border bg-card p-3 text-left text-card-foreground ring-1 ring-foreground/10 sm:p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-1">
          <h2 className="text-sm font-medium">BTC price</h2>
          <p className="text-xs text-muted-foreground">
            Window{' '}
            <span className="font-medium text-foreground">{timeRange}</span>
            {' · '}
            interval{' '}
            <span className="font-medium text-foreground">{chartInterval}</span>
            <span className="hidden sm:inline">
              {' — '}
              history loaded via simulated API (cached per range + interval).
            </span>
            {isRefreshing ? ' Refreshing…' : null}
          </p>
        </div>
        <ChartTypeSwitcher value={chartType} onChange={setChartType} />
      </div>

      <ChartIntervalSwitcher
        value={chartInterval}
        onChange={setChartInterval}
      />

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
          <ChartPanViewport data={data}>
            {({ data: panData, width, height, yDomain, compact }) =>
              chartType === 'line' ? (
                <PriceLineChart
                  data={panData}
                  width={width}
                  height={height}
                  yDomain={yDomain}
                  compact={compact}
                />
              ) : (
                <PriceCandlestickChart
                  data={panData}
                  width={width}
                  height={height}
                  yDomain={yDomain}
                  compact={compact}
                />
              )
            }
          </ChartPanViewport>
        </div>
      )}
    </section>
  )
}
