import { TriangleAlertIcon } from 'lucide-react'
import { accuracyWarningMessages } from '@/lib/predictionAccuracy'
import type { PredictionAccuracy } from '@/types/predictionAccuracy'

type PredictionAccuracyWarningProps = {
  accuracy: PredictionAccuracy
}

/**
 * The service's own low-accuracy warning, in words. Renders nothing while
 * every metric is inside its bounds.
 */
export function PredictionAccuracyWarning({
  accuracy,
}: PredictionAccuracyWarningProps) {
  const messages = accuracyWarningMessages(accuracy)

  if (messages.length === 0) {
    return null
  }

  return (
    <div
      role="status"
      aria-label="Accuracy warning"
      className="flex gap-2 rounded-md border border-warning/40 bg-warning/10 p-3 text-sm"
    >
      <TriangleAlertIcon
        aria-hidden="true"
        className="mt-0.5 size-4 shrink-0 text-warning"
      />
      <div className="flex flex-col gap-1">
        <p className="font-medium">Treat recent forecasts with caution</p>
        {messages.map((message) => (
          <p key={message} className="text-muted-foreground">
            {message}
          </p>
        ))}
      </div>
    </div>
  )
}
