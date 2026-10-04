import { useState } from 'react'
import { IndicatorHistoryFilter } from '@/components/dashboard/indicators/IndicatorHistoryFilter'
import { MacroIndicatorHistoryTable } from '@/components/dashboard/indicators/MacroIndicatorHistoryTable'
import { PriceChart } from '@/components/dashboard/PriceChart'
import { MacroIndicators } from '@/components/dashboard/MacroIndicators'
import { useMacroIndicatorHistoryQuery } from '@/hooks/useMacroIndicatorHistoryQuery'
import { useMacroIndicatorsQuery } from '@/hooks/useMacroIndicatorsQuery'
import { uniqueIndicatorNames } from '@/lib/macroIndicatorDisplay'
import { filterIndicatorsByName } from '@/lib/macroIndicatorHistory'
import { usePreferencesStore } from '@/stores/preferencesStore'
import type { IndicatorHistoryFilter as SeriesFilter } from '@/types/macroIndicators'

export function MacroIndicatorsSection() {
  const timeRange = usePreferencesStore((state) => state.timeRange)
  const [indicatorFilter, setIndicatorFilter] =
    useState<SeriesFilter>('all')
  const latestQuery = useMacroIndicatorsQuery()
  const historyQuery = useMacroIndicatorHistoryQuery(timeRange)
  const history = historyQuery.data ?? []
  const seriesNames =
    history.length > 0
      ? uniqueIndicatorNames(history)
      : uniqueIndicatorNames(latestQuery.data ?? [])
  const visibleHistory = filterIndicatorsByName(history, indicatorFilter)

  return (
    <div className="flex min-w-0 flex-col gap-4">
      <MacroIndicators
        indicators={latestQuery.data ?? []}
        isLoading={latestQuery.isPending}
        error={latestQuery.error}
      />

      <section
        aria-label="Price and indicator history"
        className="flex min-w-0 flex-col overflow-hidden rounded-xl border border-border bg-card text-card-foreground ring-1 ring-foreground/10"
      >
        <PriceChart
          framed={false}
          linkedIndicators={visibleHistory}
          linkedIndicatorsLoading={historyQuery.isPending}
          linkedIndicatorsError={historyQuery.error}
        />

        <div className="flex min-w-0 flex-col gap-3 px-3 pb-3 pt-1 sm:px-4 sm:pb-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0">
              <h2 className="text-sm font-medium">Indicator history</h2>
              <p className="text-xs text-muted-foreground">
                Same {timeRange} window, aligned to each BTC candle — last
                print at or before that bar. Series rebased to 100 at the
                start so different units can share one scale.
              </p>
            </div>
            <IndicatorHistoryFilter
              value={indicatorFilter}
              seriesNames={seriesNames}
              onChange={setIndicatorFilter}
            />
          </div>
        </div>
      </section>

      {!historyQuery.isPending &&
      !historyQuery.error &&
      history.length > 0 ? (
        <MacroIndicatorHistoryTable indicators={visibleHistory} />
      ) : null}
    </div>
  )
}
