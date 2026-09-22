import { PredictionStatusMessage } from '@/components/dashboard/predictions/PredictionStatusMessage'
import { PredictionSummary } from '@/components/dashboard/predictions/PredictionSummary'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import type { BtcPrediction } from '@/types/predictions'

type PredictionSummaryCardProps = {
  prediction: BtcPrediction | undefined
  isPending: boolean
  error: Error | null
}

/** Numbers behind the plot: end price, change, trend, levels and band width. */
export function PredictionSummaryCard({
  prediction,
  isPending,
  error,
}: PredictionSummaryCardProps) {
  return (
    <Card className="min-w-0">
      <CardHeader>
        <CardTitle className="text-base">Forecast summary</CardTitle>
        <CardDescription>
          {prediction
            ? `${prediction.modelName} model, ${prediction.horizon} horizon`
            : 'Model outlook for the selected window'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {prediction ? (
          <PredictionSummary prediction={prediction} />
        ) : (
          <PredictionStatusMessage isPending={isPending} error={error} />
        )}
      </CardContent>
    </Card>
  )
}
