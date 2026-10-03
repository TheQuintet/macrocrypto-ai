import {
  formatForecastAge,
  formatPredictionTime,
} from '@/components/dashboard/lib/predictionChart'
import { useNow } from '@/hooks/useNow'

type PredictionMadeAtProps = {
  predictionTime: string
}

/**
 * When the batch was generated, relative and absolute.
 *
 * Batches are produced on a schedule and served until the next one, so a 7d
 * forecast can be most of a day old. Saying so keeps an old batch from being
 * read as current, and says what the dashed divider on the plot marks: the
 * start of this forecast, not the present moment.
 */
export function PredictionMadeAt({ predictionTime }: PredictionMadeAtProps) {
  const nowMs = useNow()
  const madeMs = new Date(predictionTime).getTime()

  if (!Number.isFinite(madeMs)) {
    return null
  }

  return (
    <p className="text-xs text-muted-foreground">
      Forecast made{' '}
      <time dateTime={predictionTime} className="font-medium text-foreground">
        {formatForecastAge(madeMs, nowMs)}
      </time>{' '}
      ({formatPredictionTime(madeMs)}). The dashed line marks where it starts.
    </p>
  )
}
