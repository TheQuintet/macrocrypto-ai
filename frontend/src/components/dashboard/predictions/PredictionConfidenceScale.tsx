import { predictionConfidencePercent } from '@/components/dashboard/lib/predictionConfidence'
import { cn } from '@/lib/utils'
import { PREDICTION_CONFIDENCE_OPTIONS } from '@/stores/predictionStore'

type PredictionConfidenceScaleProps = {
  confidence: number
}

/**
 * The coverage levels on offer, with the selected one picked out. Each is
 * set in the same colour: a higher level is a wider band, not a better one.
 */
export function PredictionConfidenceScale({
  confidence,
}: PredictionConfidenceScaleProps) {
  const selected = predictionConfidencePercent(confidence)

  return (
    <ul
      aria-label="Coverage levels"
      className="m-0 flex list-none flex-wrap gap-x-3 gap-y-1 p-0 text-[10px] leading-none text-muted-foreground"
    >
      {PREDICTION_CONFIDENCE_OPTIONS.map((option) => {
        const isSelected =
          predictionConfidencePercent(option.value) === selected

        return (
          <li
            key={option.value}
            aria-current={isSelected ? 'true' : undefined}
            className={cn(isSelected && 'font-medium text-foreground')}
          >
            {option.label}
          </li>
        )
      })}
    </ul>
  )
}
