import {
  PREDICTION_CONFIDENCE_BAND_ORDER,
  formatPredictionConfidenceBand,
  formatPredictionConfidenceBandRange,
  predictionConfidenceBandTone,
} from '@/components/dashboard/lib/predictionConfidence'
import { cn } from '@/lib/utils'

/** Always-visible key so low / moderate / high colours can be read at a glance. */
export function PredictionConfidenceScale() {
  return (
    <ul className="m-0 flex list-none flex-wrap gap-x-3 gap-y-1 p-0 text-[10px] leading-none">
      {PREDICTION_CONFIDENCE_BAND_ORDER.map((band) => (
        <li
          key={band}
          className={cn('font-medium', predictionConfidenceBandTone(band).toneClass)}
        >
          {`${formatPredictionConfidenceBand(band)} ${formatPredictionConfidenceBandRange(band)}`}
        </li>
      ))}
    </ul>
  )
}
