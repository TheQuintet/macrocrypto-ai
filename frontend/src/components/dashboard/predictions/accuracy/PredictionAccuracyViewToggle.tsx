import { Button } from '@/components/ui/button'
import type { AccuracyChartView } from '@/types/predictionAccuracy'

const VIEW_OPTIONS: { value: AccuracyChartView; label: string }[] = [
  { value: 'trend', label: 'Accuracy trend' },
  { value: 'comparison', label: 'Predicted vs actual' },
]

type PredictionAccuracyViewToggleProps = {
  view: AccuracyChartView
  onViewChange: (view: AccuracyChartView) => void
}

/** Switches the card's chart between the accuracy trend and the comparison. */
export function PredictionAccuracyViewToggle({
  view,
  onViewChange,
}: PredictionAccuracyViewToggleProps) {
  return (
    <div
      className="flex flex-wrap items-center gap-1.5"
      role="group"
      aria-label="Accuracy chart"
    >
      {VIEW_OPTIONS.map((option) => (
        <Button
          key={option.value}
          type="button"
          size="sm"
          variant={view === option.value ? 'default' : 'outline'}
          aria-pressed={view === option.value}
          className="min-h-11 touch-manipulation sm:min-h-7"
          onClick={() => onViewChange(option.value)}
        >
          {option.label}
        </Button>
      ))}
    </div>
  )
}
