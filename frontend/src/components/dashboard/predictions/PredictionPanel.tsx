import { PredictionChartCard } from '@/components/dashboard/predictions/PredictionChartCard'
import { PredictionSummaryCard } from '@/components/dashboard/predictions/PredictionSummaryCard'
import { PredictionAccuracyCard } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyCard'
import { useBtcPredictionHistoryQuery } from '@/hooks/useBtcPredictionHistoryQuery'
import { useBtcPredictionQuery } from '@/hooks/useBtcPredictionQuery'

/**
 * The Forecasts screen's content: one chart and one summary, both reading the
 * horizon and confidence chosen in the chart card's controls, and underneath
 * them how accurate past forecasts at that horizon turned out to be.
 *
 * History and forecast are separate queries because they fail separately: the
 * candles come through the gateway, the forecast does not yet, so the chart
 * must still draw when only one of them arrives.
 */
export function PredictionPanel() {
  const { data, isPending, error } = useBtcPredictionQuery()
  const history = useBtcPredictionHistoryQuery()

  return (
    <div className="grid grid-cols-1 gap-3 sm:gap-4 lg:grid-cols-3">
      <PredictionChartCard
        prediction={data}
        candles={history.data?.candles}
        isPending={isPending}
        error={error}
      />
      <PredictionSummaryCard
        prediction={data}
        isPending={isPending}
        error={error}
      />
      <PredictionAccuracyCard />
    </div>
  )
}
