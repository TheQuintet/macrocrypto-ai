import { useMemo, useState } from 'react'
import { PredictionStatusMessage } from '@/components/dashboard/predictions/PredictionStatusMessage'
import { PredictionAccuracyComparison } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyComparison'
import { PredictionAccuracyDetailsDialog } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyDetailsDialog'
import { PredictionAccuracyMarketTiles } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyMarketTiles'
import { PredictionAccuracySummary } from '@/components/dashboard/predictions/accuracy/PredictionAccuracySummary'
import { PredictionAccuracyTrendChart } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyTrendChart'
import { PredictionAccuracyViewToggle } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyViewToggle'
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
import {
  accuracyTrendGapNote,
  formatModelName,
} from '@/lib/predictionAccuracy'
import { usePredictionStore } from '@/stores/predictionStore'
import type {
  AccuracyChartView,
  PredictionAccuracy,
} from '@/types/predictionAccuracy'

/**
 * How often the model has been right, for the horizon on the chart above —
 * the reason a trader should (or should not) lean on the forecast.
 *
 * The score, figures, markets and predicted-vs-actual follow the chart's
 * 24h/7d toggle. The trend is the exception: it always draws both horizons
 * so they can be compared, which is why both are fetched.
 */
export function PredictionAccuracyCard() {
  const horizon = usePredictionStore((state) => state.horizon)
  const [view, setView] = useState<AccuracyChartView>('trend')
  const [detailsOpen, setDetailsOpen] = useState(false)
  const dayQuery = usePredictionAccuracyQuery('24h')
  const weekQuery = usePredictionAccuracyQuery('7d')
  const { data: accuracy, isPending, error } =
    horizon === '24h' ? dayQuery : weekQuery
  const trend = useMemo(
    () =>
      [dayQuery.data, weekQuery.data].filter(
        (entry): entry is PredictionAccuracy => entry != null,
      ),
    [dayQuery.data, weekQuery.data],
  )
  const trendGapNotes = [
    accuracyTrendGapNote('24h', dayQuery.data, dayQuery.error),
    accuracyTrendGapNote('7d', weekQuery.data, weekQuery.error),
  ].filter((note): note is string => note != null)
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
              className="min-h-11 touch-manipulation sm:min-h-7"
              onClick={() => setDetailsOpen(true)}
            >
              View details
            </Button>
          </CardAction>
        ) : null}
      </CardHeader>

      <CardContent className="flex min-w-0 flex-col gap-6">
        {accuracy ? (
          <>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
              <PredictionAccuracySummary accuracy={accuracy} />
              <div className="flex min-w-0 flex-col gap-3">
                <PredictionAccuracyViewToggle
                  view={view}
                  onViewChange={setView}
                />
                {view === 'trend' ? (
                  <PredictionAccuracyTrendChart
                    accuracies={trend}
                    gapNotes={trendGapNotes}
                  />
                ) : (
                  <PredictionAccuracyComparison
                    horizon={horizon}
                    modelName={accuracy.modelName}
                  />
                )}
              </div>
            </div>
            <PredictionAccuracyMarketTiles accuracy={accuracy} />
          </>
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
          trend={trend}
          trendGapNotes={trendGapNotes}
          open={detailsOpen}
          onOpenChange={setDetailsOpen}
        />
      ) : null}
    </Card>
  )
}
