import { PredictionHorizonToggle } from '@/components/dashboard/predictions/PredictionHorizonToggle'
import { PredictionStatusMessage } from '@/components/dashboard/predictions/PredictionStatusMessage'
import { PredictionAccuracyComparisonChart } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyComparisonChart'
import { usePredictionAccuracyPointsQuery } from '@/hooks/usePredictionAccuracyPointsQuery'
import { formatModelName } from '@/lib/predictionAccuracy'
import type { PredictionHorizon } from '@/types/predictions'

type PredictionAccuracyComparisonProps = {
  horizon: PredictionHorizon
  /** The model the card grades, so both describe the same forecasts. */
  modelName: string
}

/**
 * Predicted against actual price, with its own loading and failure states.
 *
 * Carries its own 24h/7d toggle, since the page's sits on the forecast card
 * out of view. It is the same store value, so flipping either one moves the
 * forecast chart, the whole accuracy card and this chart together.
 */
export function PredictionAccuracyComparison({
  horizon,
  modelName,
}: PredictionAccuracyComparisonProps) {
  const { data, isPending, error } = usePredictionAccuracyPointsQuery(
    horizon,
    modelName,
  )

  return (
    <div className="flex w-full min-w-0 flex-col gap-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="min-w-0 flex-1 text-xs text-muted-foreground">
          Each {horizon} forecast from {formatModelName(modelName)} against the
          price it was for
        </p>
        <PredictionHorizonToggle label="Comparison horizon" />
      </div>
      {data && data.points.length > 0 ? (
        // Keyed by horizon so a new window opens fully zoomed out.
        <PredictionAccuracyComparisonChart
          key={horizon}
          points={data.points}
          horizon={horizon}
        />
      ) : (
        <PredictionStatusMessage
          isPending={isPending}
          error={error}
          unavailableTitle="Comparison unavailable"
          emptyMessage={`No ${horizon} forecasts scored yet`}
        />
      )}
    </div>
  )
}
