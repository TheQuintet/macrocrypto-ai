import { PredictionSummaryStat } from '@/components/dashboard/predictions/PredictionSummaryStat'
import { PredictionAccuracyWarning } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyWarning'
import {
  accuracyScore,
  accuracyScoreExplanation,
  accuracyScoreLabel,
  findThreshold,
  formatAccuracyDate,
  formatAccuracyPercent,
  formatAccuracyPeriod,
  formatErrorPercent,
  formatSampleCount,
  formatUsdMiss,
  scoreThreshold,
  thresholdToneClass,
} from '@/lib/predictionAccuracy'
import { cn } from '@/lib/utils'
import type { PredictionAccuracy } from '@/types/predictionAccuracy'

type PredictionAccuracySummaryProps = {
  accuracy: PredictionAccuracy
}

/**
 * Headline score, the service's warning, and the plain-language figures.
 * Only figures the service grades are coloured; the rest are plain facts.
 */
export function PredictionAccuracySummary({
  accuracy,
}: PredictionAccuracySummaryProps) {
  const score = accuracyScore(accuracy.metrics)
  const scoreTone = score
    ? thresholdToneClass(scoreThreshold(score.kind, accuracy.thresholds))
    : ''
  const toneFor = (metric: string) =>
    thresholdToneClass(findThreshold(accuracy.thresholds, metric))

  return (
    <div className="flex flex-col gap-4">
      <PredictionAccuracyWarning accuracy={accuracy} />

      <div role="group" aria-label="Accuracy score">
        <p className="text-xs text-muted-foreground">
          {score ? accuracyScoreLabel(score.kind) : 'Accuracy'}
        </p>
        <p
          className={cn(
            'font-mono text-3xl font-semibold tabular-nums',
            scoreTone || 'text-foreground',
          )}
        >
          {formatAccuracyPercent(score?.value)}
        </p>
        <p className="text-sm text-muted-foreground">
          {score
            ? accuracyScoreExplanation(score.kind, accuracy.metrics)
            : 'Not enough scored forecasts yet'}
        </p>
      </div>

      <div className="flex flex-col gap-2">
        <PredictionSummaryStat
          label="Typical miss"
          value={formatUsdMiss(accuracy.metrics.mae)}
          className={toneFor('mae_pct')}
        />
        <PredictionSummaryStat
          label="Large misses"
          value={formatUsdMiss(accuracy.metrics.rmse)}
          className={toneFor('rmse_pct')}
        />
        <PredictionSummaryStat
          label="Average % miss"
          value={formatErrorPercent(accuracy.metrics.mape)}
          className={toneFor('mape')}
        />
        <PredictionSummaryStat
          label="Forecasts checked"
          value={formatSampleCount(accuracy.samples)}
        />
        <PredictionSummaryStat
          label="Period"
          value={formatAccuracyPeriod(accuracy.periodDays)}
        />
        <PredictionSummaryStat
          label="Last scored"
          value={formatAccuracyDate(accuracy.lastUpdated)}
        />
      </div>
    </div>
  )
}
