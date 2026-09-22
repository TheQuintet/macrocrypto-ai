import { Button } from '@/components/ui/button'
import {
  PREDICTION_CONFIDENCE_OPTIONS,
  usePredictionStore,
} from '@/stores/predictionStore'

/** Picks the confidence level the endpoint computes its bounds at. */
export function ConfidenceLevelSelector() {
  const confidence = usePredictionStore((state) => state.confidence)
  const setConfidence = usePredictionStore((state) => state.setConfidence)

  return (
    <div
      className="flex flex-wrap items-center gap-1.5 sm:gap-2"
      role="group"
      aria-label="Confidence level"
    >
      {PREDICTION_CONFIDENCE_OPTIONS.map((option) => (
        <Button
          key={option.value}
          type="button"
          size="sm"
          variant={confidence === option.value ? 'default' : 'outline'}
          aria-pressed={confidence === option.value}
          className="min-h-11 min-w-12 touch-manipulation sm:min-h-7"
          onClick={() => setConfidence(option.value)}
        >
          {option.label}
        </Button>
      ))}
    </div>
  )
}
