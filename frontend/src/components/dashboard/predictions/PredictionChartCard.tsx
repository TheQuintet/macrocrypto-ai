import {
  isFullyZoomedOut,
  PREDICTION_ZOOM_MAX,
} from '@/components/dashboard/lib/predictionZoom'
import { ChartZoomControls } from '@/components/dashboard/controls/ChartZoomControls'
import { usePredictionStore } from '@/stores/predictionStore'
import { ConfidenceLevelSelector } from '@/components/dashboard/predictions/ConfidenceLevelSelector'
import { PredictionChart } from '@/components/dashboard/predictions/PredictionChart'
import { PredictionChartLegend } from '@/components/dashboard/predictions/PredictionChartLegend'
import { PredictionHorizonToggle } from '@/components/dashboard/predictions/PredictionHorizonToggle'
import { PredictionMadeAt } from '@/components/dashboard/predictions/PredictionMadeAt'
import { PredictionStatusMessage } from '@/components/dashboard/predictions/PredictionStatusMessage'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import type { ChartCandle } from '@/types/chart'
import type { BtcPrediction } from '@/types/predictions'

type PredictionChartCardProps = {
  prediction: BtcPrediction | undefined
  candles: ChartCandle[] | undefined
  isPending: boolean
  error: Error | null
}

/** The forecast plot, with the horizon and confidence controls that drive it. */
export function PredictionChartCard({
  prediction,
  candles,
  isPending,
  error,
}: PredictionChartCardProps) {
  const historyZoom = usePredictionStore((state) => state.historyZoom)
  const zoomHistory = usePredictionStore((state) => state.zoomHistory)
  const hasChart = Boolean(prediction && prediction.points.length > 0)

  // Every point the endpoint returns is a forecast; there is no fit to exclude.
  const forecastCount = prediction?.points.length ?? 0
  const availableCandles = candles?.length ?? 0
  /**
   * Inverted on purpose: the control disables its minus at `min`, and showing
   * *more* history is zooming out — so the value it reads has to fall as the
   * window widens. It bottoms out early once every fetched candle is on
   * screen, which is what stops the minus doing nothing.
   */
  const zoomValue = isFullyZoomedOut(
    historyZoom,
    forecastCount,
    availableCandles,
  )
    ? 0
    : PREDICTION_ZOOM_MAX - historyZoom
  const canZoom = hasChart && availableCandles > forecastCount

  return (
    <Card className="min-w-0 lg:col-span-2">
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2">
          Price forecast
          {prediction?.source === 'simulated' ? (
            <Badge variant="outline" className="text-[10px] font-normal">
              Simulated
            </Badge>
          ) : null}
        </CardTitle>
        <CardDescription>
          Projected price path with its confidence band
        </CardDescription>
        <CardAction>
          <PredictionHorizonToggle />
        </CardAction>
      </CardHeader>

      <CardContent className="flex min-w-0 flex-col gap-3">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <span className="text-xs text-muted-foreground">
            Confidence level
          </span>
          <ConfidenceLevelSelector />
          {canZoom ? (
            <div className="ms-auto flex items-center gap-2">
              <span className="hidden text-xs text-muted-foreground sm:inline">
                History
              </span>
              <ChartZoomControls
                value={zoomValue}
                min={0}
                max={PREDICTION_ZOOM_MAX}
                onZoomIn={() => zoomHistory('in')}
                onZoomOut={() => zoomHistory('out')}
              />
            </div>
          ) : null}
        </div>
        {hasChart && prediction ? (
          <>
            <PredictionChart
              prediction={prediction}
              candles={candles}
              historyZoom={historyZoom}
            />
            <PredictionMadeAt predictionTime={prediction.predictionTime} />
            <PredictionChartLegend
              confidence={prediction.confidence}
              hasHistory={(candles?.length ?? 0) > 0}
            />
          </>
        ) : (
          <PredictionStatusMessage
            isPending={isPending}
            error={error}
            skeletonClassName="h-56 w-full sm:h-[280px] md:h-[340px]"
          />
        )}
      </CardContent>
    </Card>
  )
}
