import { PredictionAccuracyMarketTile } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyMarketTile'
import {
  findThreshold,
  marketGrade,
  marketGradeLegend,
} from '@/lib/predictionAccuracy'
import type { PredictionAccuracy } from '@/types/predictionAccuracy'

type PredictionAccuracyMarketTilesProps = {
  accuracy: PredictionAccuracy
}

/** How accurate the model has been in each kind of market, two by two on a phone. */
export function PredictionAccuracyMarketTiles({
  accuracy,
}: PredictionAccuracyMarketTilesProps) {
  const mapeThreshold = findThreshold(accuracy.thresholds, 'mape')

  return (
    <section className="flex flex-col gap-2" aria-label="Accuracy by market">
      <h3 className="text-sm font-medium">By market condition</h3>
      {accuracy.marketBreakdown.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No market-condition breakdown for this window yet.
        </p>
      ) : (
        <>
          <ul className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {accuracy.marketBreakdown.map((row) => (
              <PredictionAccuracyMarketTile
                key={row.condition}
                row={row}
                grade={marketGrade(
                  row.mape,
                  accuracy.metrics.mape,
                  mapeThreshold,
                )}
              />
            ))}
          </ul>
          <p className="text-xs text-muted-foreground">
            {marketGradeLegend(mapeThreshold)}
          </p>
        </>
      )}
    </section>
  )
}
