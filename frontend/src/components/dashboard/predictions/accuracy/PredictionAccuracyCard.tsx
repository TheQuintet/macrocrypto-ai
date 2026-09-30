import { useState } from 'react'
import { PredictionStatusMessage } from '@/components/dashboard/predictions/PredictionStatusMessage'
import { PredictionAccuracyDetailsDialog } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyDetailsDialog'
import { PredictionAccuracySummary } from '@/components/dashboard/predictions/accuracy/PredictionAccuracySummary'
import { PredictionAccuracyTrendChart } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyTrendChart'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { usePredictionAccuracyQuery } from '@/hooks/usePredictionAccuracyQuery'
import { accuracyScore, formatModelName } from '@/lib/predictionAccuracy'

/**
 * How often the model has been right, for the horizon on the chart above —
 * the reason a trader should (or should not) lean on the forecast.
 */
export function PredictionAccuracyCard() {
  const { data: accuracy, isPending, error } = usePredictionAccuracyQuery()
  const [detailsOpen, setDetailsOpen] = useState(false)
  const score = accuracy ? accuracyScore(accuracy.metrics) : null
  const modelLabel = accuracy
    ? `${formatModelName(accuracy.modelName)}${accuracy.isBestModel ? ' · best model' : ''}`
    : null

  return (
    <Card className="min-w-0 lg:col-span-3">
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2 text-base">
          Forecast accuracy
          {accuracy?.source === 'simulated' ? (
            <Badge variant="outline" className="text-[10px] font-normal">
              Simulated
            </Badge>
          ) : null}
        </CardTitle>
        <CardDescription>
          {accuracy
            ? `${modelLabel}, past ${accuracy.horizon} forecasts checked against the real price`
            : 'How past forecasts compared with the real price'}
        </CardDescription>
        {accuracy ? (
          <CardAction>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDetailsOpen(true)}
            >
              View details
            </Button>
          </CardAction>
        ) : null}
      </CardHeader>

      <CardContent>
        {accuracy ? (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
            <PredictionAccuracySummary accuracy={accuracy} />
            {score ? (
              <PredictionAccuracyTrendChart
                history={accuracy.history}
                kind={score.kind}
                thresholds={accuracy.thresholds}
              />
            ) : null}
          </div>
        ) : (
          <PredictionStatusMessage
            isPending={isPending}
            error={error}
            unavailableTitle="Accuracy unavailable"
            emptyMessage="No forecasts have been scored for this horizon yet"
          />
        )}
      </CardContent>

      {accuracy ? (
        <PredictionAccuracyDetailsDialog
          accuracy={accuracy}
          open={detailsOpen}
          onOpenChange={setDetailsOpen}
        />
      ) : null}
    </Card>
  )
}
