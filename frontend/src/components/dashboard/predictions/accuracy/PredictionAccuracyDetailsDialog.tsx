import { PredictionAccuracyBreakdownTable } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyBreakdownTable'
import { PredictionAccuracyThresholdTable } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyThresholdTable'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  findThreshold,
  formatAccuracyPercent,
  formatAccuracyPeriod,
  formatErrorPercent,
  formatModelName,
  formatUsdMiss,
  thresholdToneClass,
} from '@/lib/predictionAccuracy'
import { cn } from '@/lib/utils'
import type { PredictionAccuracy } from '@/types/predictionAccuracy'

type PredictionAccuracyDetailsDialogProps = {
  accuracy: PredictionAccuracy
  open: boolean
  onOpenChange: (open: boolean) => void
}

/** The full scorecard: every metric, each market, and each quality check. */
export function PredictionAccuracyDetailsDialog({
  accuracy,
  open,
  onOpenChange,
}: PredictionAccuracyDetailsDialogProps) {
  const { metrics } = accuracy
  const version = accuracy.modelVersion ? ` v${accuracy.modelVersion}` : ''
  /** Tint a figure by the check that grades it (MAE/RMSE via their % bounds). */
  const toneFor = (metric: string) =>
    cn(
      'text-right tabular-nums',
      thresholdToneClass(findThreshold(accuracy.thresholds, metric)),
    )

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Forecast accuracy details</DialogTitle>
          <DialogDescription>
            {formatModelName(accuracy.modelName)}
            {version}, {accuracy.horizon} forecasts,{' '}
            {formatAccuracyPeriod(accuracy.periodDays).toLowerCase()}
          </DialogDescription>
        </DialogHeader>

        {/*
          Only the body scrolls, so the title stays put. The negative margin
          moves the scrollbar into the panel's own padding, clear of the
          right-aligned figures.
        */}
        <div className="scrollbar-slim -mr-4 flex max-h-[65vh] flex-col gap-6 overflow-y-auto pr-4">
          <section className="flex flex-col gap-2">
            <h3 className="text-sm font-medium">Error metrics</h3>
            <dl className="grid grid-cols-[1fr_auto] gap-x-6 gap-y-1 text-sm">
              <dt className="text-muted-foreground">Direction called right</dt>
              <dd className={toneFor('directional_accuracy')}>
                {formatAccuracyPercent(metrics.directionalAccuracy)}
              </dd>

              <dt className="text-muted-foreground">Typical miss (MAE)</dt>
              <dd className={toneFor('mae_pct')}>
                {formatUsdMiss(metrics.mae)}
              </dd>

              <dt className="text-muted-foreground">
                Large-miss error (RMSE, weights big misses more)
              </dt>
              <dd className={toneFor('rmse_pct')}>
                {formatUsdMiss(metrics.rmse)}
              </dd>

              <dt className="text-muted-foreground">Average % miss (MAPE)</dt>
              <dd className={toneFor('mape')}>
                {formatErrorPercent(metrics.mape)}
              </dd>
            </dl>
          </section>

          <section className="flex flex-col gap-2">
            <h3 className="text-sm font-medium">By market condition</h3>
            <PredictionAccuracyBreakdownTable rows={accuracy.marketBreakdown} />
          </section>

          <section className="flex flex-col gap-2">
            <h3 className="text-sm font-medium">Quality checks</h3>
            <p className="text-xs text-muted-foreground">
              A warning is raised after {accuracy.warningThresholdDays} days in a
              row outside a bound.
            </p>
            <PredictionAccuracyThresholdTable thresholds={accuracy.thresholds} />
          </section>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
