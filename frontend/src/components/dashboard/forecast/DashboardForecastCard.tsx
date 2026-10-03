import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { DashboardForecastFigures } from '@/components/dashboard/forecast/DashboardForecastFigures'
import { PredictionChart } from '@/components/dashboard/predictions/PredictionChart'
import { PredictionChartLegend } from '@/components/dashboard/predictions/PredictionChartLegend'
import { PredictionStatusMessage } from '@/components/dashboard/predictions/PredictionStatusMessage'
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
import { routes } from '@/constants/navigation'
import { useBtcPredictionHistoryQueryFor } from '@/hooks/useBtcPredictionHistoryQuery'
import { useBtcPredictionQueryFor } from '@/hooks/useBtcPredictionQuery'
import type { PredictionParams } from '@/types/predictions'

/**
 * Always the next day at the default coverage, whatever the Forecasts screen
 * has selected. The same params give the same query key, so moving between
 * the two pages reuses one cached batch.
 */
const DASHBOARD_FORECAST: PredictionParams = { horizon: '24h', confidence: 0.85 }

/** Shorter than the Forecasts screen's plot: this card sits above the price chart. */
const CHART_HEIGHT_CLASS_NAME = 'h-48 sm:h-56'

/**
 * The 24h forecast on the dashboard: the Forecasts screen's chart at a
 * compact height, its headline figures beside it, and a way through to the
 * full screen.
 *
 * The candles are a separate query that can fail on its own; the forecast
 * still draws without them, as it does on the Forecasts screen.
 */
export function DashboardForecastCard() {
  const { data, isPending, error } =
    useBtcPredictionQueryFor(DASHBOARD_FORECAST)
  const history = useBtcPredictionHistoryQueryFor(DASHBOARD_FORECAST.horizon)
  const candles = history.data?.candles
  const hasChart = Boolean(data && data.points.length > 0)

  return (
    <Card className="min-w-0">
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2">
          Next 24 hours
          {data?.source === 'simulated' ? (
            <Badge variant="outline" className="text-[10px] font-normal">
              Simulated
            </Badge>
          ) : null}
        </CardTitle>
        <CardDescription>
          Projected BTC price with its confidence band
        </CardDescription>
        <CardAction>
          <Button asChild variant="outline" className="h-10 sm:h-8">
            <Link to={routes.forecasts}>
              Open forecasts
              <ArrowRight aria-hidden="true" />
            </Link>
          </Button>
        </CardAction>
      </CardHeader>

      <CardContent className="min-w-0">
        {hasChart && data ? (
          <div className="grid min-w-0 grid-cols-1 gap-4 lg:grid-cols-3 lg:gap-6">
            <div className="flex min-w-0 flex-col gap-3 lg:col-span-2">
              <PredictionChart
                prediction={data}
                candles={candles}
                heightClassName={CHART_HEIGHT_CLASS_NAME}
              />
              <PredictionChartLegend
                confidence={data.confidence}
                hasHistory={(candles?.length ?? 0) > 0}
              />
            </div>
            <DashboardForecastFigures prediction={data} />
          </div>
        ) : (
          <PredictionStatusMessage
            isPending={isPending}
            error={error}
            skeletonClassName={`${CHART_HEIGHT_CLASS_NAME} w-full`}
          />
        )}
      </CardContent>
    </Card>
  )
}
