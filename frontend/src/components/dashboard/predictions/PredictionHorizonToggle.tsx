import { Button } from '@/components/ui/button'
import {
  PREDICTION_HORIZON_OPTIONS,
  usePredictionStore,
} from '@/stores/predictionStore'

/**
 * Switches the whole screen between the 24h and 7d forecast windows — one
 * control for both horizons, since chart, summary and key levels all read
 * from the same selection.
 */
export function PredictionHorizonToggle() {
  const horizon = usePredictionStore((state) => state.horizon)
  const setHorizon = usePredictionStore((state) => state.setHorizon)

  return (
    <div
      className="flex flex-wrap items-center justify-end gap-1.5 sm:gap-2"
      role="group"
      aria-label="Forecast horizon"
    >
      {PREDICTION_HORIZON_OPTIONS.map((option) => (
        <Button
          key={option.value}
          type="button"
          size="sm"
          variant={horizon === option.value ? 'default' : 'outline'}
          aria-pressed={horizon === option.value}
          className="min-h-11 min-w-12 touch-manipulation sm:min-h-7"
          onClick={() => setHorizon(option.value)}
        >
          {option.label}
        </Button>
      ))}
    </div>
  )
}
