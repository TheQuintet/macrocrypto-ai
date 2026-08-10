import { useMemo, useState } from 'react'
import { PriceBarChart } from '@/dashboard/bar-chart'
import { ChartIntervalSwitcher } from '@/dashboard/chart-interval-switcher'
import {
  DEFAULT_CHART_INTERVAL,
  type ChartInterval,
} from '@/dashboard/chart-interval'
import { ChartPanViewport } from '@/dashboard/chart-pan'
import { mapHistoryPointsToChartPoints } from '@/dashboard/chart-point'
import {
  ChartTypeSwitcher,
  type ChartType,
} from '@/dashboard/chart-type-switcher'
import { PriceLineChart } from '@/dashboard/line-chart'
import { useBtcPriceHistoryQuery } from '@/hooks/use-btc-price-history-query'
import { usePreferencesStore } from '@/stores/preferences-store'

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

    return mapHistoryPointsToChartPoints(
      historyQuery.data.points,
      historyQuery.data.interval,
    )
  }, [historyQuery.data])

  const isInitialLoading = historyQuery.isPending && data.length === 0
  const isRefreshing = historyQuery.isFetching && data.length > 0

  return (
    <section className="flex w-full max-w-xl flex-col gap-3 rounded-lg border p-4 text-left">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <h2 className="text-sm font-medium">BTC price</h2>
          <p className="text-xs text-muted-foreground">
            Window{' '}
            <span className="font-medium text-foreground">{timeRange}</span>
            {' · '}
            interval{' '}
            <span className="font-medium text-foreground">{chartInterval}</span>
            {' — '}
            history loaded via simulated API (cached per range + interval).
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
        <ChartPanViewport data={data}>
          {({ data: panData, width, height, yDomain }) =>
            chartType === 'line' ? (
              <PriceLineChart
                data={panData}
                width={width}
                height={height}
                yDomain={yDomain}
              />
            ) : (
              <PriceBarChart
                data={panData}
                width={width}
                height={height}
                yDomain={yDomain}
              />
            )
          }
        </ChartPanViewport>
      )}
    </section>
  )
}
